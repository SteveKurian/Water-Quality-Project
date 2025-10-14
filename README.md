# Water Quality Data Service

The **Water Quality Project** is a full data pipeline that processes and visualizes water quality observations. It begins by loading raw CSV files, cleaning the data using the **z-score method** to remove outliers, and storing the cleaned dataset in a **NoSQL database** (MongoDB or mongomock). A **Flask REST API** is built to provide access to the data through endpoints that support filtering, statistics, and outlier detection. The project also includes a **Streamlit client** that communicates with the API to display tables, summary statistics, and interactive **Plotly visualizations**, such as line charts, histograms, and scatter plots. Together, these components demonstrate a complete **ETL (Extract, Transform, Load)** workflow and showcase how to integrate data cleaning, API design, and interactive visualization in a unified system.

---

## Data Sources

- **Dataset**: [Water Quality Dataset](./data/2022-nov16.csv)  
This dataset contains raw water quality observations collected in November 2022, including fields such as temperature, salinity, dissolved oxygen (ODO), and other sensor readings used for cleaning, analysis, and visualization in this project.

---

## Authors

This project was completed in collaboration with the following for the class CIS3590: Internship Ready Software Development

- Shatoya Gardner
- Shirina Shaji Daniel
- Steve Kurian
