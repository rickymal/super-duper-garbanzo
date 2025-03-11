def fibonacci_time(start_interval=0, iterations=10):
    """
    Gera uma sequência de tempo baseada na sequência de Fibonacci.

    Parâmetros:
    - start_interval (int): O índice inicial da sequência de Fibonacci.
    - iterations (int): O número de iterações desejadas.

    Yield:
    - str: Uma string representando o tempo no formato adequado (minutos, horas, dias, semanas, etc.).
    """
    def fibonacci_sequence(n):
        """Gera a sequência de Fibonacci até o n-ésimo índice."""
        a, b = 0, 1
        for _ in range(n):
            yield a
            a, b = b, a + b

    # Gerar a sequência completa
    sequence = list(fibonacci_sequence(start_interval + iterations))
    sequence = sequence[start_interval:]  # Ignorar os índices iniciais indesejados

    for value in sequence:
        weeks = value // 10080  # 60 * 24 * 7
        remaining_minutes = value % 10080

        days = remaining_minutes // 1440  # 60 * 24
        remaining_minutes %= 1440

        hours = remaining_minutes // 60
        minutes = remaining_minutes % 60

        time_str = []
        if weeks > 0:
            time_str.append(f"{weeks}w")
        if days > 0:
            time_str.append(f"{days}d")
        if hours > 0:
            time_str.append(f"{hours}h")
        if minutes > 0:
            time_str.append(f"{minutes}m")

        yield " ".join(time_str)


for val in fibonacci_time(start_interval = 2, iterations = 20):
  print(val)
