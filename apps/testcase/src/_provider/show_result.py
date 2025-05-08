from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich import box


def display_test_results(console: Console, test_results: list[tuple[str, int, str]]):
    """
    Exibe os resultados dos testes em uma tabela formatada usando Rich.

    Args:
        console (Console): Instância do Rich Console para output
        test_results (list): Lista de tuplas com (descrição, status, mensagem)
                            status 2 = sucesso, outros = falha
    """
    # Criar tabela
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Teste", width=50)
    table.add_column("Status", justify="center")
    table.add_column("Mensagem", style="dim")

    # Processar cada resultado
    for description, status, message in test_results:
        # Determinar estilo baseado no status
        if status == 2:
            status_text = Text("✓", style="bold green")
            desc_style = "green"
        else:
            status_text = Text("✗", style="bold red")
            desc_style = "red"

        # Adicionar linha à tabela
        table.add_row(
            Text(description, style=desc_style),
            status_text,
            message
        )

    # Calcular resumo
    total_tests = len(test_results)
    passed = sum(1 for _, status, _ in test_results if status == 2)
    failed = total_tests - passed

    # Exibir tabela
    console.print(table)

    # Exibir resumo
    console.print("\n[bold]Resumo:[/bold]")
    console.print(f"  Total:   {total_tests}")
    console.print(f"  [green]Sucesso:[/green] {passed}")
    console.print(f"  [red]Falha:[/red]    {failed}")

    # Exibir mensagem final
    if failed == 0:
        console.print("\n[bold green]🎉 Todos os testes passaram com sucesso![/bold green]")
    else:
        console.print(f"\n[bold red]❌ {failed} teste(s) falharam![/bold red]")
