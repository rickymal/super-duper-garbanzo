
import time
from rich.console import Console
from rich.live import Live
from rich.text import Text

def sleep_com_contagem_regressiva(console: Console, segundos: int):
    """
    Pausa a execução por 'segundos' e exibe uma contagem regressiva no console.

    Args:
        console: Uma instância de rich.console.Console para exibir a saída.
        segundos: O número inteiro de segundos para esperar e contar.
    """
    if not isinstance(segundos, int) or segundos < 0:
        console.print("[bold red]Erro: O tempo em segundos deve ser um número inteiro não negativo.[/bold red]")
        return

    # Usa rich.live para atualizar a mesma linha no terminal
    # transient=True faz a contagem desaparecer após a conclusão
    with Live(console=console, auto_refresh=False, transient=True) as live:
        for i in range(segundos, -1, -1):
            # Cria o texto a ser exibido (pode usar Text para mais estilo)
            if i == 1:
                mensagem = f"Aguarde: {i} segundo restante..."
            else:
                mensagem = f"Aguarde: {i} segundos restantes..."

            # Atualiza o conteúdo do Live e força a atualização da tela
            live.update(Text(mensagem, style="yellow"), refresh=True)

            # Pausa por 1 segundo, exceto após exibir "0 segundos"
            if i > 0:
                time.sleep(1)
            else:
                # Uma pequena pausa no final para garantir que "0 segundos" seja visível
                time.sleep(0.1)

    # Opcional: Mensagem após a conclusão da contagem (já fora do Live)
    # console.print("[bold green]Contagem concluída![/bold green]")

# --- Exemplo de Uso ---
if __name__ == "__main__":
    # 1. Crie uma instância do Console do rich
    meu_console = Console()

    # 2. Defina o tempo de espera
    tempo_de_espera = 10  # Esperar por 10 segundos

    meu_console.print(f"Iniciando uma pausa de {tempo_de_espera} segundos com contagem regressiva...")

    # 3. Chame a função passando o console e o tempo
    sleep_com_contagem_regressiva(meu_console, tempo_de_espera)

    meu_console.print("Pausa finalizada. O programa continua.")

    # Exemplo com tempo inválido
    meu_console.print("\nTentando com tempo inválido:")
    sleep_com_contagem_regressiva(meu_console, -5)