from dataclasses import dataclass, asdict
import os
from dataclasses import dataclass
import random
from datetime import datetime

class Fakers:
    def __init__(self,):
        # Simulando a leitura de um arquivo yaml para carregar dados fictícios
        self.data = {
            "primeiro nome": ["Henrique", "Alessandro", "Carmélio", "Gabriel", "Eduardo"],
            "ultimo nome": ["Moura", "Borges", "Silva", "Santos", "Oliveira"],
            "dominio": ["gmail.com", "yahoo.com", "outlook.com"]
        }

    def get_sequencial_dates(self, numbers, min_interval, max_interval, start):
        # Simulando a geração de datas sequenciais
        return [start.strftime('%Y-%m-%dT%H:%M:%S') for _ in range(numbers)]

    def select_one(self, *keys):
        results = [random.choice(self.data[key]) for key in keys]
        return " ".join(results)
