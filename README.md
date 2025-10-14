# Water-Quality-Project

### Project Description

The **Water Quality Project** is a full data pipeline that processes and visualizes water quality observations. It begins by loading raw CSV files, cleaning the data using the **z-score method** to remove outliers, and storing the cleaned dataset in a **NoSQL database** (MongoDB or mongomock). A **Flask REST API** is built to provide access to the data through endpoints that support filtering, statistics, and outlier detection. The project also includes a **Streamlit client** that communicates with the API to display tables, summary statistics, and interactive **Plotly visualizations**, such as line charts, histograms, and scatter plots. Together, these components demonstrate a complete **ETL (Extract, Transform, Load)** workflow and showcase how to integrate data cleaning, API design, and interactive visualization in a unified system.
---
## Authors

This project was completed in collaboration with:

- Shatoya Gardner
- Shirina Shaji Daniel
- Steve Kurian
