from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QAction, QCheckBox, QLabel, QPushButton
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QLocale, QVariant, Qt, QMetaType, QT_VERSION_STR
from qgis.core import (
    QgsProject, QgsWkbTypes, QgsField, QgsCoordinateTransform,
    QgsCoordinateReferenceSystem, QgsGeometry, QgsVectorLayer,
    QgsFeature, Qgis, QgsMessageLog, QgsUnitTypes
)
from qgis.utils import iface
import os

class MeasureCalculatorPlugin:
    """Measure Calculator Plugin for QGIS"""

    def __init__(self, iface):
        self.iface = iface
        self.dialog = None

    def initGui(self):
        """Initialize plugin interface"""
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        self.action = QAction(
            QIcon(icon_path),
            self.tr("Measure Calculator"),
            self.iface.mainWindow()
        )
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu(self.tr("Measure Calculator"), self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        """Remove plugin from interface"""
        self.iface.removePluginMenu(self.tr("Measure Calculator"), self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        """Main execution flow"""
        try:
            layer = iface.activeLayer()
            if not layer:
                self.show_message(
                    self.tr("Warning"),
                    self.tr("No active layer selected!"),
                    Qgis.Warning
                )
                return

            if not layer.selectedFeatures():
                self.show_message(
                    self.tr("Warning"),
                    self.tr("No features selected in active layer!"),
                    Qgis.Warning
                )
                return

            self.dialog = CalculatorDialog(layer, self.iface)
            DialogExec(self.dialog)

        except Exception as e:
            self.show_message(self.tr("Error"), str(e), Qgis.Critical)

    def show_message(self, title, message, level):
        """Show messages in QGIS message bar"""
        self.iface.messageBar().pushMessage(
            title,
            message,
            level=level,
            duration=3
        )

    def tr(self, text):
        """Translation system"""
        translations = {
            "Measure Calculator": "Calculadora de Medidas",
            "Warning": "Aviso",
            "No active layer selected!": "Nenhuma camada ativa selecionada!",
            "No features selected in active layer!": "Não há feições selecionadas na camada ativa!",
            "Error": "Erro",
            "Layer is already in edit mode!": "Camada já está em modo de edição!",
            "Save or cancel edits before proceeding.": "Salve ou cancele as edições antes de continuar."
        }
        if QLocale().name().startswith('pt'):
            return translations.get(text, text)
        return text

class CalculatorDialog(QDialog):
    """Main calculation dialog"""

    MAX_CRS_DISPLAY = 10

    def __init__(self, layer, iface):
        super().__init__()
        self.iface = iface
        self.layer = layer
        self.results = {
            'total': 0,
            'area': [],
            'perimeter': [],
            'length': [],
            'utm': {},
            'conic': {},
            'geom_type': layer.geometryType(),
            'all_crs': set()
        }
        self.setup_ui()
        self.calculate_measures()
        self.setWindowTitle(self.tr("Measure Calculator"))
        self.setMinimumSize(400, 300)

    def setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout()
        
        self.lbl_results = QLabel()
        self.lbl_results.setTextFormat(QtRichText)
        self.lbl_results.setWordWrap(True)
        self.lbl_results.setTextInteractionFlags(QtTextSelectableByMouse)
        self.lbl_results.setStyleSheet("""
            QLabel {
                border: 1px solid #cccccc;
                padding: 5px;
                border-radius: 3px;
                margin: 2px;
            }
        """)
        layout.addWidget(self.lbl_results)

        self.chk_update = QCheckBox(self.tr("Update fields in original layer"))
        self.chk_update.setEnabled(not self.layer.isEditable() and self.layer.geometryType() != QgsWkbTypes.PointGeometry)
        layout.addWidget(self.chk_update)

        self.chk_temp = QCheckBox(self.tr("Create temporary layer"))
        layout.addWidget(self.chk_temp)

        self.btn_ok = QPushButton(self.tr("OK"))
        self.btn_ok.clicked.connect(self.process)
        layout.addWidget(self.btn_ok)

        self.setLayout(layout)

    def calculate_measures(self):
        """Perform measurements calculation"""
        try:
            for feat in self.layer.selectedFeatures():
                geom = feat.geometry()
                src_crs = self.layer.crs()
                
                centroid = self.transform_centroid(geom, src_crs)
                crs = self.select_crs(geom, src_crs, centroid)
                
                xform = QgsCoordinateTransform(src_crs, crs, QgsProject.instance())
                geom.transform(xform)

                if self.results['geom_type'] == QgsWkbTypes.PolygonGeometry:
                    self.results['area'].append(geom.area() / 10000)
                    self.results['perimeter'].append(geom.length() / 1000)
                elif self.results['geom_type'] == QgsWkbTypes.LineGeometry:
                    self.results['length'].append(geom.length() / 1000)

                self.count_crs(crs)
                self.results['total'] += 1

            self.display_results()

        except Exception as e:
            self.iface.messageBar().pushMessage(
                self.tr("Error"),
                str(e),
                Qgis.Critical,
                3
            )

    def transform_centroid(self, geometry, src_crs):
        transform = QgsCoordinateTransform(
            src_crs,
            QgsCoordinateReferenceSystem('EPSG:4326'),
            QgsProject.instance()
        )
        return transform.transform(geometry.centroid().asPoint())

    def select_crs(self, geometry, src_crs, centroid):
        bbox = geometry.boundingBox()
        transform = QgsCoordinateTransform(src_crs, QgsCoordinateReferenceSystem('EPSG:4326'), QgsProject.instance())
        transform.transformBoundingBox(bbox)
        
        if (bbox.xMaximum() - bbox.xMinimum()) > 5.9:
            crs = QgsCoordinateReferenceSystem('ESRI:54034')
        else:
            utm_zone = int((centroid.x() + 180) // 6) + 1
            epsg = 32600 + utm_zone if centroid.y() >= 0 else 32700 + utm_zone
            crs = QgsCoordinateReferenceSystem(f'EPSG:{epsg}')
            
        self.results['all_crs'].add(crs.authid())
        return crs

    def count_crs(self, crs):
        authid = crs.authid()
        if 'ESRI:54034' in authid:
            self.results['conic'][authid] = self.results['conic'].get(authid, 0) + 1
        else:
            self.results['utm'][authid] = self.results['utm'].get(authid, 0) + 1

    def get_project_units(self):
        """Retorna as unidades de medida configuradas no projeto"""
        return {
            'area': QgsProject.instance().areaUnits(),
            'distance': QgsProject.instance().distanceUnits()
        }

    def convert_to_project_units(self, value, unit_type):
        """
        Converte valores para as unidades do projeto
        Retorna tupla (valor_convertido, símbolo_unidade)
        """
        units = self.get_project_units()
        
        if unit_type == 'area':
            base_value = value * 10000  # Converte ha para m²
            if units['area'] == QgsUnitTypes.AreaSquareMeters:
                return (base_value, "m²")
            elif units['area'] == QgsUnitTypes.AreaSquareKilometers:
                return (base_value / 1e6, "km²")
            elif units['area'] == QgsUnitTypes.AreaHectares:
                return (value, "ha")
            elif units['area'] == QgsUnitTypes.AreaSquareMiles:
                return (base_value * 3.861e-7, "mi²")
            elif units['area'] == QgsUnitTypes.AreaSquareYards:
                return (base_value * 1.19599, "yd²")
            elif units['area'] == QgsUnitTypes.AreaSquareFeet:
                return (base_value * 10.7639, "ft²")
            elif units['area'] == QgsUnitTypes.AreaAcres:
                return (base_value * 0.000247105, "acres")
            
        elif unit_type == 'distance':
            base_value = value * 1000  # Converte km para metros
            if units['distance'] == QgsUnitTypes.DistanceMeters:
                return (base_value, "m")
            elif units['distance'] == QgsUnitTypes.DistanceKilometers:
                return (value, "km")
            elif units['distance'] == QgsUnitTypes.DistanceFeet:
                return (base_value * 3.28084, "ft")
            elif units['distance'] == QgsUnitTypes.DistanceYards:
                return (base_value * 1.09361, "yd")
            elif units['distance'] == QgsUnitTypes.DistanceMiles:
                return (base_value * 0.000621371, "mi")
            elif units['distance'] == QgsUnitTypes.DistanceNauticalMiles:
                return (base_value * 0.000539957, "nmi")
            elif units['distance'] == QgsUnitTypes.DistanceCentimeters:
                return (base_value * 100, "cm")
            elif units['distance'] == QgsUnitTypes.DistanceMillimeters:
                return (base_value * 1000, "mm")
            
        return (value, "")

    def display_results(self):
        msg = f"<b>{self.tr('RESULTS')}</b><br><br>"
        
        if self.results['geom_type'] == QgsWkbTypes.PolygonGeometry:
            total_area = sum(self.results['area'])
            area_proj, area_unit = self.convert_to_project_units(total_area, 'area')
            msg += (
                f"<b>{self.tr('Total Area')}:</b> {self.format_number(total_area)} ha<br>"
                f"&nbsp;&nbsp;&nbsp;&nbsp;{self.format_number(area_proj)} {area_unit}<br>"
            )

            total_perim = sum(self.results['perimeter'])
            perim_proj, perim_unit = self.convert_to_project_units(total_perim, 'distance')
            msg += (
                f"<b>{self.tr('Total Perimeter')}:</b> {self.format_number(total_perim)} km<br>"
                f"&nbsp;&nbsp;&nbsp;&nbsp;{self.format_number(perim_proj)} {perim_unit}<br><br>"
            )
            
        elif self.results['geom_type'] == QgsWkbTypes.LineGeometry:
            total_length = sum(self.results['length'])
            length_proj, length_unit = self.convert_to_project_units(total_length, 'distance')
            msg += (
                f"<b>{self.tr('Total Length')}:</b> {self.format_number(total_length)} km<br>"
                f"&nbsp;&nbsp;&nbsp;&nbsp;{self.format_number(length_proj)} {length_unit}<br><br>"
            )
        
        msg += f"<b>{self.tr('Processed Features')}:</b> {self.results['total']}<br><br>"
        msg += self.build_crs_section()
        
        self.lbl_results.setText(msg)
        self.log_to_message_panel(msg)
        self.iface.messageBar().pushMessage(
            self.tr("Success"),
            self.tr("Calculations completed"),
            Qgis.Success,
            3
        )

    def build_crs_section(self):
        section = ""
        utm_items = list(self.results['utm'].items())
        conic_items = list(self.results['conic'].items())
        
        if utm_items:
            section += f"<b>{self.tr('UTM Projection')}:</b><br>"
            for crs, count in utm_items[:self.MAX_CRS_DISPLAY]:
                section += f"- {crs} ({self.crs_name(crs)})<br>{count} {self.tr('features')}<br>"
            if len(utm_items) > self.MAX_CRS_DISPLAY:
                section += f"... ({len(utm_items)-self.MAX_CRS_DISPLAY} {self.tr('more')})<br>"
        
        if conic_items:
            section += f"<br><b>{self.tr('Conic Projection')}:</b><br>"
            for crs, count in conic_items[:self.MAX_CRS_DISPLAY]:
                section += f"- {crs} ({self.crs_name(crs)})<br>{count} {self.tr('features')}<br>"
            if len(conic_items) > self.MAX_CRS_DISPLAY:
                section += f"... ({len(conic_items)-self.MAX_CRS_DISPLAY} {self.tr('more')})<br>"
        
        return section

    def log_to_message_panel(self, msg):
        """Log formatado incluindo as unidades do projeto"""
        clean_msg = (
            msg.replace("<br>", "\n")
            .replace("<b>", "")
            .replace("</b>", "")
            .replace("&nbsp;", " ")
        )
        QgsMessageLog.logMessage(
            clean_msg,
            "Calculadora de Medidas",
            Qgis.Info
        )

    def crs_name(self, authid):
        crs = QgsCoordinateReferenceSystem(authid)
        return crs.description() if crs.isValid() else self.tr("Unknown CRS")

    def format_number(self, value):
        return QLocale().toString(float(value), 'f', 4)

    def process(self):
        try:
            if self.chk_update.isChecked():
                self.update_fields()
            
            if self.chk_temp.isChecked():
                self.create_temp_layer()
            
            self.layer.removeSelection()
            self.accept()

        except Exception as e:
            self.iface.messageBar().pushMessage(
                self.tr("Error"),
                str(e),
                Qgis.Critical,
                3
            )

    def update_fields(self):
        try:
            if self.layer.isEditable():
                raise Exception(
                    self.tr("Layer is already in edit mode!") + "\n" +
                    self.tr("Save or cancel edits before proceeding.")
                )  # Fechamento do raise

            if not self.layer.startEditing():
                raise Exception(self.tr("Layer is not editable!"))

            fields = []
            if self.results['geom_type'] == QgsWkbTypes.PolygonGeometry:
                fields = ['area_ha', 'perim_km']
            elif self.results['geom_type'] == QgsWkbTypes.LineGeometry:
                fields = ['length_km']

            # Adiciona campos e atualiza
            self.add_fields(fields)
            self.layer.updateFields()  # Garante reconhecimento dos novos campos
            self.populate_fields(fields)

            # Commit das alterações
            if self.layer.commitChanges():
                self.iface.messageBar().pushMessage(
                    self.tr("Success"),
                    self.tr("Fields updated successfully"),
                    Qgis.Success,
                    3
                )

        except Exception as e:
            self.layer.rollBack()
            self.iface.messageBar().pushMessage(
                self.tr("Error"),
                str(e),
                Qgis.Critical,
                3
            )

    def add_fields(self, fields):
        provider = self.layer.dataProvider()
        existing = [field.name() for field in provider.fields()]
        
        new_fields = []
        for field in fields:
            if field not in existing:
                new_field = QgsField(field, QVariantDouble, 'double', 20, 4)
                new_fields.append(new_field)
        
        if new_fields:
            if not provider.addAttributes(new_fields):
                raise Exception(self.tr("Failed to add fields!"))
            
            # self.layer.updateFields() # Moved to update_fields function

    def populate_fields(self, fields):
        try:
            for idx, feat in enumerate(self.layer.selectedFeatures()):
                values = {}
                if self.results['geom_type'] == QgsWkbTypes.PolygonGeometry:
                    values = {
                        'area_ha': round(self.results['area'][idx], 4),
                        'perim_km': round(self.results['perimeter'][idx], 4)
                    }
                elif self.results['geom_type'] == QgsWkbTypes.LineGeometry:
                    values = {'length_km': round(self.results['length'][idx], 4)}
                
                for field, value in values.items():
                    field_idx = self.layer.fields().lookupField(field)
                    if field_idx == -1:
                        raise Exception(self.tr("Field not found:") + f" {field}")
                    
                    if not self.layer.changeAttributeValue(feat.id(), field_idx, value):
                        raise Exception(self.tr("Error updating feature ID:") + f" {feat.id()}")

        except IndexError:
            raise Exception(self.tr("Mismatch between features and calculations!"))

    def create_temp_layer(self):
        try:
            geom_type = 'Polygon' if self.results['geom_type'] == QgsWkbTypes.PolygonGeometry else 'LineString'
            temp_layer = QgsVectorLayer(
                f"{geom_type}?crs={self.layer.crs().authid()}",
                self.tr("Calculated Measures"),
                "memory"
            )

            provider = temp_layer.dataProvider()
            original_fields = self.layer.fields().toList()
            
            if self.results['geom_type'] == QgsWkbTypes.PolygonGeometry:
                original_fields.extend([
                    QgsField("area_ha", QVariantDouble, 'double', 20, 4),
                    QgsField("perim_km", QVariantDouble, 'double', 20, 4)
                ])
            else:
                original_fields.append(QgsField("length_km", QVariantDouble, 'double', 20, 4))

            provider.addAttributes(original_fields)
            temp_layer.updateFields()

            temp_layer.startEditing()
            for idx, feat in enumerate(self.layer.selectedFeatures()):
                new_feat = QgsFeature(temp_layer.fields())
                new_feat.setGeometry(feat.geometry())
                
                for i in range(self.layer.fields().count()):
                    new_feat.setAttribute(i, feat.attribute(i))
                
                if self.results['geom_type'] == QgsWkbTypes.PolygonGeometry:
                    new_feat["area_ha"] = round(self.results['area'][idx], 4)
                    new_feat["perim_km"] = round(self.results['perimeter'][idx], 4)
                else:
                    new_feat["length_km"] = round(self.results['length'][idx], 4)

                provider.addFeature(new_feat)

            temp_layer.commitChanges()
            QgsProject.instance().addMapLayer(temp_layer)
            self.iface.messageBar().pushMessage(
                self.tr("Success"),
                self.tr("Temporary layer created"),
                Qgis.Success,
                3
            )

        except Exception as e:
            raise Exception(self.tr("Error creating temporary layer:") + f" {str(e)}")

    def tr(self, text):
        translations = {
            "Measure Calculator": "Calculadora de Medidas",
            "Update fields in original layer": "Atualizar campos na camada original",
            "Create temporary layer": "Criar camada temporária",
            "OK": "OK",
            "RESULTS": "RESULTADOS",
            "Total Area": "Área Total",
            "Total Perimeter": "Perímetro Total", 
            "Total Length": "Comprimento Total",
            "Processed Features": "Feições Processadas",
            "UTM Projection": "Projeção UTM",
            "Conic Projection": "Projeção Policônica",
            "features": "feições",
            "Unknown CRS": "CRS Desconhecido",
            "Success": "Sucesso",
            "Calculations completed": "Cálculos concluídos",
            "Layer is not editable! Consider creating a temporary layer to include the"
            " calculated fields.": "Camada não é editável! Considere criar uma camada "
            "temporária para incluir os campos calculados.",
            "Fields updated successfully": "Campos atualizados com sucesso",
            "Temporary layer created": "Camada temporária criada",
            "Failed to add fields!": "Falha ao adicionar campos!",
            "Field not found:": "Campo não encontrado:",
            "Error updating feature ID:": "Erro ao atualizar feição ID:",
            "Mismatch between features and calculations!": "Incompatibilidade entre feições e cálculos!",
            "Error creating temporary layer:": "Erro ao criar camada temporária:",
            "more": "mais",
            "square meters": "metros quadrados",
            "square kilometers": "quilômetros quadrados",
            "square miles": "milhas quadradas",
            "square yards": "jardas quadradas",
            "square feet": "pés quadrados",
            "acres": "acres",
            "miles": "milhas",
            "yards": "jardas",
            "feet": "pés",
            "nautical miles": "milhas náuticas",
            "centimeters": "centímetros",
            "millimeters": "milímetros"
        }
        if QLocale().name().startswith('pt'):
            return translations.get(text, text)
        return text

# Compatibility check for Qt version
if QT_VERSION_STR.startswith('5.'):
    QVariantDouble = QVariant.Double
    DialogExec = lambda dialog: dialog.exec_()
    QtRichText = Qt.RichText
    QtTextSelectableByMouse = Qt.TextSelectableByMouse
else:
    QVariantDouble = QMetaType.Type.Double
    DialogExec = lambda dialog: dialog.exec()
    QtRichText = Qt.TextFormat.RichText
    QtTextSelectableByMouse = Qt.TextInteractionFlag.TextSelectableByMouse
