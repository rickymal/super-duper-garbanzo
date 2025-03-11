
import os

import yaml


class YamlSerializer:
    # serializer = YamlSerializer(folder = 'mock')
    def __init__(self, folder: str, name: str):
        self.folder = folder
        self.name = name
        self.data = None

    def save(self, data: dict, extra_path=[]):
        # Cria o caminho completo do diretório
        full_path = os.path.join(self.folder, *extra_path)
        if not os.path.isdir(full_path):
            os.makedirs(full_path)  # Cria todos os diretórios necessários
        
        # Define o caminho completo do arquivo (pode ser ajustado conforme necessário)
        file_path = os.path.join(full_path, self.name)
        with open(file_path, 'w') as f:
            self.data = data
            yaml.dump(data, f)

    def load(self, extra_path = []):
        full_path = os.path.join(self.folder, *extra_path)
        file_path = os.path.join(full_path, self.name)
        with open(file_path, 'r') as f:
            self.data = yaml.safe_load(f)
            return self.data

    def has_file(self):
        return self.data is not None

