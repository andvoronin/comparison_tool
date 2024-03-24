# Tool to Compare Two Sources in Semi-Automatic Mode

## Components
The tool consists of three main components:
- Comparison Runner
- Launcher
- Helpers

## Comparison Runner
The Comparison Runner, a Jupyter notebook (`comparison_runner.ipynb`), runs the primary logic for data comparison. It compares two datasets, provided as .csv files, in one run. To do the comparison, three main parameters need to be set up:
- Path to the source file (string)
- Path to the target file (string)
- Column mapping between the source and target files (list)

Column mapping is a list where each element is a dictionary specifying the mapping between one column in the source and one column in the target. The mapping dictionary may include the following parameters:
* **source_name**: (string, required) Name of the column in the source .csv file
* **target_name**: (string, required) Name of the column in the target .csv file
* **key**: (boolean, required). If it is set to True, the columns will be used as keys to join the extracts. If it's False, the column will be used for comparison.
* **comparison**: (string, optional) Only applicable (and required) if `key` equals False. The type of comparison to use. Available options:
    * **numeric** - Compares based on the difference between the columns
    * **string** - Compares based on the exact values of the columns
* **replace_nulls**: (string, optional) Only applicable if `key` equals False. If set, NULLs in the comparison columns will be replaced by zeros (for numeric comparison) or empty string (for string comparison). Consider using this option if NULLs are expected in the comparison columns. Otherwise, NULL values might not appear in the result dataset as a discrepancy. Available options: 
    * **source** - Replaces NULLs in the source extract only
    * **target** - Replaces NULLs in the target extract (NaN and numpy inf are both considered NULLs)
    * **both** - Replaces NULLs in both extracts
* **clean**: (string, optional) Only applicable if `key` equals False and `comparison` equals `numeric`. Removes spaces, dollar signs, and percentage signs in the source or target csv. Available options: 
    * **source** - Cleans data in the column of the source extract
    * **target** - Cleans data in the column of the target extract
    * **both** - Cleans data in the columns of both extracts
* **precision**: (integer, optional) Only applicable if `key` equals False and `comparison` equals `numeric`. This determines the number of digits after the decimal point in the subtraction result to consider as a discrepancy.
* **negative_format**: (object, optional) Only applicable if `key` equals False and `comparison` equals `numeric`. This handles formats for negative numbers in the dataset. It's set up using two parameters:
    * **type** - Currently, only **parentheses** is supported. It replaces the enclosed value in parentheses with the equivalent negative number, e.g., (156.23) -> -156.23
    * **value** - Specifies in which extract the handling should be done. Available options:
        * **source** - Applies negative number formatting in the source extract
        * **target** - Applies negative number formatting in the target extract
        * **both** - Applies negative number formatting in both extracts
* **ignore_case**: (boolean, optional) Only applicable if `key` equals False and `comparison` equals `string`. If set to True, it ignores the case during the comparison.

<details>
<summary>Column mapping example</summary>

```
 columns = [
    {'source_name': 'key_column_1', 'target_name': 'key_column_1', 'key': True},
    {'source_name': 'key_column_2', 'target_name': 'key_column_2', 'key': True},
    {'source_name': 'key_column_3', 'target_name': 'key_column_3', 'key': True},

    {'source_name': 'qty','target_name': 'quantity', 'key': False, 'comparison': 'numeric', 'clean': 'target', 'replace_nulls': 'both', 'precision': 0, 'negative_format': {'type':'parentheses', 'value':'both'}},
    {'source_name': '% of Total','target_name': '% of Total', 'key': False, 'comparison': 'numeric', 'clean': 'target','replace_nulls': 'both', 'precision': 3}
    ]
```

</details>

Using parameters set in the code is referred to as "Standalone Mode" and can be used for any ad-hoc data comparison requests. In Standalone Mode, the following required variables should be assigned in the `comparison_runner.ipynb` file:
- **standalone_mode** should be set to True
- **test_name** should be a descriptive name of the comparison. This is used only to organize testing results.
- **src_extract_path** and **tgt_extract_path** are paths to the source and target files that need to be compared.
- **columns** should be assigned to a column mapping between the source and target (see the description above).

Setting up a comparison using a .json file requires creating a file named `params.json` with all the required parameters. The `params.json` file should be saved in the same folder as the `comparison_runner.ipynb` notebook. The file contains the following elements:
- **name**: (string, required) A descriptive name of the comparison/test.
- **source_path**: (string, required) File path of the first file being compared.
- **target_path**: (string, required) File path of the second file being compared.
- **column_mapping**: (list, required) Column mapping between source and target (see the description above).

<details>
<summary>Example of the <i>params.json</i> file</summary>

```
{
    "name": "14_totals_scatterplot",
    "source_path": "c:\\Users\\avv\\Documents\\src.csv",
    "target_path": "c:\\Users\\avv\\Documents\\tgt.csv",
    "column_mapping": [
        {
            "source_name": "Origin Area",
            "target_name": "Origin Area",
            "key": true
        },
        {
            "source_name": "usd_amount",
            "target_name": "amount",
            "key": false,
            "comparison": "numeric",
            "clean": "both",
            "replace_nulls": "both",
            "precision": 3
        }
    ]
}
```

</details>

## Launcher
The Launcher is a Jupyter notebook (`launcher.ipynb`) that serves as a wrapper around the Comparison Runner, performing the following tasks:
- Fetching data from multiple sources and passing the data to the Comparison Runner in the required (csv) format
- Running multiple comparisons at one run
  
Specifications for each comparison should be stored in the `test_configs` subfolder. When executed, the Launcher searches for `.json` files in the `test_configs` folder. For each found config file, it retrieves the source and target data, converts it to `.csv`, and creates a `params.json` file with the parameters required for the Comparison Runner. Each configuration file contains three main elements:
- **source**: This is the description of the source data (object). 
- **target**: This is the description of the target data (object).
- **column_mapping**: Column mapping between source and target (list).

The structure of the description for the source and target data is parallel and depends on the type of the data source used to retrieve data. The description contains one required element, `type` (string), with all other elements being type-dependent. This means all parameters will vary based on the value of the `type` parameter. Currently, two types of data sources are supported:
- **flat_file**
- **sql_query**

### Loading Data from a Flat File
The type `flat_file` represents data fetched from a file in the file system. For the flat file source, two parameters need to be defined:
- **format**: (string, required) Currently, the only supported value is `csv`.
- **file_path**: (string, required) Specifies the path to the file to be loaded.
<details>
<summary>Example of the <i>source</i> loaded from the csv file</summary>

```
    "source": {
        "type": "flat_file",
        "format": "csv",
        "file_path": "C:\\Extracts\\scatterplot_2.csv"
    }
```

</details>

### Loading Data Using SQL Query
The `sql_query` type implies fetching data by running an SQL query against an SQL database (Synapse Dedicated SQL pool). Currently, only Interactive login using Azure MFA authentication is supported.  When retrieving data using an SQL query, two parameters must be defined:
- **environment**: This should be the name of the Synapse environment (`qa` / `prod`). The mapping between the environment name and connection strings is stored in the `env_settings.json` file.
- **file_path**: Specifies the path to the `.sql` file containing the SQL query that should be executed.

### Column mapping
Column mapping is set using the same format as used by *Comparison runner* as described in the [Comparison runner section](#comparison-runner)

<details>
<summary>Example of the json config file created for the Launcher</summary>

```
{
    "source": {
        "type": "flat_file",
        "format": "csv",
        "file_path": "C:\\Users\\path_to_extract\\file1.csv"
    },
    "target": {
        "type": "sql_query",
        "environment": "prod_val",
        "file_path": "C:\\Users\\path_to_folder_with query\\query1.sql"
    },
    "column_mapping": [
        {
            "source_name": "Origin Area",
            "target_name": "Origin Area",
            "key": true
        },
        {
            "source_name": "usd_amount",
            "target_name": "amount",
            "key": false,
            "comparison": "numeric",
            "clean": "both",
            "replace_nulls": "both",
            "precision": 3
        }
    ]
}
```

</details>

## Helpers
Helpers are used to process data from different sources and manage JSON-based configurations for the Launcher. They are also designed to support additional data source types handled by the tool. Helpers are classes defined in the `comparisonHelper.py` file. The main helpers are as follows:
- **TestParamsReader**: This class serves as the entry point for reading .json configs located in the `test_configs` folder. It holds information about every config found.
- **TestDescription**: This represents the attributes of a single config file (source/target/column mapping).
- **SourceDescription**: This is an abstract base class that describes types of data sources used to retrieve data. There are two classes inherited from `SourceDescription`:
    - **SourceDescriptionFlat** handles logic for the `flat_file` type of data source. (See the [Loading data from a flat file](#loading-data-from-a-flat-file) section for reference.)
    - **SourceDescriptionSQL** handles logic for the `sql_query` type. (See the [Loading data using SQL query](#loading-data-using-sql-query) section for reference.)

   Additional source types can be implemented as separate classes inherited from `SourceDescription` and should implement the following methods:
   - `save_to_csv(self, file_path)`: Implements logic to save data to a .csv file at the specified `file_path`.
   - `get_description_errors(self)`: Checks if data settings for the data source are set up correctly. It returns a list of found errors. An empty list means all settings are correct.
   - `get_columns(self)`: Returns the list of columns in the dataset.