import json
import pyodbc
import os
import pandas as pd
import shutil
from abc import ABC, abstractmethod

class SourceDescription(ABC):
    def __init__(self, description):
        self.description = description
        self.type = description['type']

    @abstractmethod
    def save_to_csv(self, file_path):
        """Save the data exracted from source to .csv file

        Args:
            file_path (string): local path to save the file
        """
        pass

    @abstractmethod
    def get_description_errors(self):
        """Check if settings for the Datasource (source/targe in terms of comparison) are set correctly
        """
        pass
    
    @abstractmethod
    def get_columns(self):
        """Get the list of the columns extracted from the Datasource
        """
        pass
        

class SourceDescriptionFlat(SourceDescription):
    # for flat files 
    def __init__(self, description):
        super().__init__(description)
        self.file_path = description.get('file_path')

    def get_description_errors(self):
        errors = []
        if self.file_path:
            if os.path.isfile(self.file_path):
                pass
            else:
                errors.append(f'Couldn\'t read the source file "{self.file_path}"')
        else:
            errors.append('Source type "flat_file" should contain the required attribute "file_path"')

        return errors

    def save_to_csv(self, file_path):
        shutil.copyfile(self.file_path, file_path)

    def get_columns(self):
        df = pd.read_csv(self.file_path)
        return df.columns.copy()


class SourceDescriptionSQL(SourceDescription):

    settings_file_path = 'env_settings.json'

    @staticmethod
    def get_environments():
        """Get the list of the available environments and their parameters

        Returns:
            list of dictionaries, with enviroment_name as key and list of environment parameters as values
        """
        if os.path.exists(SourceDescriptionSQL.settings_file_path):
            with open(SourceDescriptionSQL.settings_file_path, 'r') as f: 
                return json.load(f)
        else:
            raise(Exception(f'Could not initiazize environments, failed to read the file {SourceDescriptionSQL.settings_file_path}'))

     

    def __init__(self, description):
        super().__init__(description)

        self.connection_string = ''
        if not self.get_description_errors():
            env_name = self.description['environment']
            available_envs = SourceDescriptionSQL.get_environments()
            connection_params = available_envs[env_name]
            server = connection_params['server']
            database = connection_params['database']
            connection_string_builder = {
            'DRIVER': '{ODBC Driver 17 for SQL Server}', 
            'SERVER': server,
            'DATABASE': database,
            'Authentication': 'ActiveDirectoryInteractive',
            'Encrypt': 'yes'
            }
            self.connection_string = ";".join([f'{name}={value}' for (name,value) in connection_string_builder.items()])

            # read_query
            self.filepath = description['file_path']
            with open(self.filepath ,"r") as f:
                self.query = f.read()
    
    def fetch_data(self):
        """ Run SQL query 

        Returns:
            Dataframe: Query execution result as Pandas Dataframe
        """
        if self.connection_string:
            try:
                cnn = pyodbc.connect(self.connection_string)
                with cnn.execute(self.query) as cursor:
                    columns = [value[0] for value in cursor.description]
                    df = pd.DataFrame.from_records(cursor.fetchall(), columns=columns)
                    return df
            finally:
                cnn.close()
        else:
            raise(Exception('Unable to initialize connection to the Database'))

    def save_to_csv(self, file_path):
        df = self.fetch_data()
        df.to_csv(file_path, index=False)


    def get_description_errors(self):
        errors = []
        available_envs = SourceDescriptionSQL.get_environments()
        if 'environment' in self.description:
            env_name = self.description['environment']
            if env_name in (available_envs):
                query_path = self.description['file_path']
                if query_path:
                    if os.path.isfile(query_path):
                        pass
                    else:
                        errors.append(f'Couldn\'t read the source file "{query_path}"')
                else:
                    errors.append(f'Source type "sql_query" should contain the required attribute "file_path"')
            else:
                errors.append(f'Unable to read settings for environment {self.env_name}')
        else:
            errors.append(f'Source type "sql_query" should contain the required attribute "environment"')
        return errors

    def get_columns(self):
        # TO-DO Limit number of rows fetched for getting the column list
        df = self.fetch_data()
        return df.columns.copy()   



class TestDescription:
    """Contains information about one single comparison to be done
    """

    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.column_mapping = description['column_mapping']
        if True: # TO-DO check correctness of the file here
            self.source_config = self.init_data_source(description['source'])
            self.target_config = self.init_data_source(description['target'])
        else:
            pass # Exception that file is incorrect

    def init_data_source(self, settings):
        if settings['type'] == 'flat_file':
            config = SourceDescriptionFlat(settings)
        elif settings['type'] == 'sql_query':
            config = SourceDescriptionSQL(settings)
        return config 

    def get_description_errors(self):
        errors = []
        source_errors = self.source_config.get_description_errors()
        if source_errors:
            errors.append('Incorrect settings for source: ' + '\n'.join(source_errors))

        target_errors =  self.target_config.get_description_errors()
        if target_errors:
            errors.append('Incorrect settings for target: ' + '\n'.join(target_errors))
        
        if not errors:
            if 'column_mapping' in self.description:
                column_mapping = self.description['column_mapping']
                if isinstance(column_mapping, list):
                    source_columns = self.source_config.get_columns()
                    target_columns = self.target_config.get_columns()
                    column_errors = []
                    required_attributes_populated = True
                    for column in column_mapping:
                        if 'source_name' in column:
                            source_name = column['source_name']
                            if not source_name in source_columns:
                                column_errors.append(f'"{source_name}" doesn\'t exist in the source')
                        else:
                            required_attributes_populated = False

                        if 'target_name' in column:
                            target_name = column['target_name']
                            if not target_name in target_columns:
                                column_errors.append(f'"{target_name}" doesn\'t exist in the target')
                        else:
                            required_attributes_populated = False

                        if not 'key' in column:
                            required_attributes_populated = False

                    if not required_attributes_populated:
                        errors.append('Each column in the mapping should have required attributes: "source_name", "target_name", "key"')
                    
                    if column_errors:
                        errors.append('Column mapping errors: ' + '\n'.join(column_errors))


                else:
                    errors.append('Column_mapping should be set as an array of columns')

            else:
                errors.append('Test description should contain the required attribute "column_mapping"')

        return errors


class TestParamsReader:

    test_config_folder = 'test_configs'
    
    def __init__(self):
        self.test_config_files_all = []
        self.load_configs()


    def load_configs(self):
        """ Read all .json config files

        After loading configs as list can be read from the all_configs property
        Correctness of the files is not checked during loading,
         use the get_description_errors() method of the TestDescription object to check if data in the json is correct  
        """
        if os.path.exists(self.test_config_folder):
            for file_name in os.listdir(self.test_config_folder):
                test_name, file_extension = os.path.splitext(os.path.basename(file_name))
                full_file_name = os.path.join(self.test_config_folder, file_name)
                if os.path.isfile(full_file_name) and file_extension.lower() =='.json':
                    with open(full_file_name, 'r') as f:
                        params = json.load(f)
                    test_descr = TestDescription(test_name, params)
                    self.test_config_files_all.append(test_descr)
        else:
            raise(Exception(f'Folder {self.test_config_folder} not found. Unable to read testing config files'))


    @property
    def all_configs(self):
        return self.test_config_files_all
           
    

