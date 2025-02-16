# QGIS Measure Calculator Plugin

## Description

The **Measure Calculator Plugin** is a robust tool for QGIS that provides precise geometric measurements (area, perimeter, length) for selected features in vector layers. It stands out for its **accuracy**, **flexibility**, and **ease of use**, even in projects with complex coordinate systems.

## Key Features

*   **Accurate Calculation with Automatic Reprojection:** To ensure maximum accuracy, the plugin **internally reprojects features** to the most appropriate Coordinate Reference System (CRS):
    *   **UTM:** For features contained within a single UTM zone.
    *   **Polyconic Projection (ESRI:54034):** For features that span multiple UTM zones, ensuring accurate calculations even for large areas. This reprojection is done *regardless* of the original CRS of the layer or the QGIS project, eliminating distortions and errors.
*   **Multiple Projection Support:** Identifies and lists the UTM and conic projections used, showing the count of features in each.
*   **Configurable Units:** Displays results in the units defined in the QGIS project settings (meters, kilometers, hectares, etc.).
*   **Data Update:** Allows updating the fields of the original layer with the calculated values (if the layer is not in edit mode).
*   **Temporary Layer Creation:** Offers the option to create a temporary layer with the results, preserving the original layer.
*   **Detailed Reports:** Displays a summary of the calculations in the interface and in the QGIS message log panel, including the units of measure used.
*   **Intuitive Interface:** Simple dialog with clear options to control the process.
*   **Localization:** Interface available in English and Portuguese.

## Installation

1.  In QGIS, go to `Plugins` -> `Manage and Install Plugins...`
2.  Search for "Measure Calculator".
3.  Click `Install Plugin`.
4.  The plugin will be available in the `Plugins` menu and on the toolbar.

## Usage

1.  **Select the desired vector layer** in the QGIS layers panel.
2.  **Select the features** for which you want to calculate measurements.
3.  Click the plugin icon (or go to `Plugins` -> `Measure Calculator`).
4.  In the plugin window:
    *   The results are displayed automatically.
    *   Check "Update fields in original layer" to add/update the `area_ha` and `perim_km` fields (polygons) or `length_km` (lines) in the original layer (if not in edit mode).
    *   Check "Create temporary layer" to create a new layer with the results.
    *   Click "OK" to process the selected options.
5.  Detailed results are also logged in the QGIS message log panel (`View` -> `Panels` -> `Log Messages`).

## Important Notes

*   **Accuracy and Calculation Types:** QGIS offers two main approaches for calculating measurements: *geodetic* calculations and *projected* calculations. Geodetic calculations are the most accurate, as they take into account the curvature of the Earth. However, they can be slower. Projected calculations, like those performed by this plugin (reprojecting to UTM or Polyconic), are faster and, in most practical cases, offer an excellent approximation. The *hybrid* approach of this plugin (UTM for smaller areas, Polyconic for larger areas) balances accuracy and performance, making it a great option for most users, regardless of the QGIS version they are using. If maximum accuracy is absolutely critical and performance is not a concern, consider using the native geodetic calculation tools in QGIS (available from version 3).
*   Make sure you have features selected before running the plugin.
*   If the layer is in edit mode, the option to update the original fields will be disabled. Save or cancel edits before using this option.
*   The display units for results (square meters, hectares, kilometers, etc.) are based on the QGIS project settings.

## Contributions

Contributions are welcome! If you find bugs, have suggestions, or want to add functionality, feel free to open an *issue* or submit a *pull request* on the GitHub repository.

## License

This plugin is distributed under the [GPLv2 or later license](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html).

## Author

Tiago José M Silva - tiago.moraessilva@hotmail.com

## Tags
area, perimeter, length, measurement, calculation, geometry, UTM, polyconic, projection, QGIS, plugin, geospatial