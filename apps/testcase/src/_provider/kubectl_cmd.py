import subprocess
import re
import argparse
from typing import List, Union, Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


def get_k8s_pod_name(namespace: str, selector: str = None, pod_regex: str = None) -> Tuple[str, str]:
    """Obtém o nome do pod mais recente usando selector ou regex."""
    try:
        if selector:
            cmd = [
                'kubectl',
                'get',
                'pod',
                f'-n={namespace}',
                f'-l={selector}',
                '--sort-by=.metadata.creationTimestamp',
                '--no-headers',
                '-o=name'
            ]
            pod = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            ).stdout.splitlines()[-1].strip()
            return pod.split('/')[-1], f"selector={selector}"

        elif pod_regex:
            cmd = [
                'kubectl',
                'get',
                'pods',
                f'-n={namespace}',
                '--no-headers',
                '-o=custom-columns=NAME:.metadata.name'
            ]
            pods = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            ).stdout.splitlines()

            matched_pods = [p.strip() for p in pods if re.fullmatch(pod_regex, p.strip())]
            if not matched_pods:
                raise ValueError(f"Nenhum pod encontrado com o padrão: {pod_regex}")

            return matched_pods[-1], f"pod_regex={pod_regex}"

        else:
            raise ValueError("Deve especificar --selector ou --pod com --use-regex")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Erro ao listar pods: {e.stderr}")
    except Exception as e:
        raise RuntimeError(str(e))


def get_k8s_logs(namespace: str, pod_name: str, tail_lines: int = 100) -> str:
    """Obtém as últimas N linhas de log de um pod no Kubernetes."""
    try:
        cmd = [
            'kubectl',
            'logs',
            f'-n={namespace}',
            pod_name,
            f'--tail={tail_lines}'
        ]
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Erro ao obter logs: {e.stderr}"
    except Exception as e:
        return f"Erro inesperado: {str(e)}"


def smart_error_grep(
        log_content: str,
        error_patterns: Union[str, List[str]],
        grep_around: int = 2,
        separator: str = "[...]"
) -> str:
    """Extrai trechos de log contendo erros com contexto ao redor."""
    if isinstance(error_patterns, str):
        error_patterns = [error_patterns]

    lines = log_content.split('\n')
    matches = []
    compiled_patterns = [re.compile(pattern) for pattern in error_patterns]

    for i, line in enumerate(lines):
        for pattern in compiled_patterns:
            if pattern.search(line):
                start = max(0, i - grep_around)
                end = min(len(lines), i + grep_around + 1)
                matches.append((start, end))
                break

    if not matches:
        return "Nenhum erro encontrado nos logs."

    matches.sort()
    consolidated = [matches[0]]
    for current in matches[1:]:
        last = consolidated[-1]
        if current[0] <= last[1]:
            consolidated[-1] = (last[0], max(last[1], current[1]))
        else:
            consolidated.append(current)

    result = []
    last_end = 0
    for start, end in consolidated:
        if start > last_end and last_end != 0:
            result.append(separator)
        result.extend(lines[start:end])
        last_end = end

    return '\n'.join(result)


def print_styled_logs(
        title: str,
        filtered_logs: str,
        color: Optional[str] = "green",
        width: Optional[int] = None
):
    """Imprime logs filtrados no console com formatação estilizada usando Rich (sem caixa)."""
    console = Console(width=width)
    styled_text = Text()

    # Adiciona o título
    styled_text.append(f"{title}\n", style=f"bold {color}")

    # Formata as linhas de log
    for line in filtered_logs.split('\n'):
        if any(error in line.lower() for error in ['error', 'exception', 'fail']):
            styled_text.append(line + "\n", style=f"bold {color}")
        elif any(warn in line.lower() for warn in ['warn', 'warning']):
            styled_text.append(line + "\n", style="bold yellow")
        else:
            styled_text.append(line + "\n", style="dim white")

    # Imprime diretamente o texto formatado
    console.print(styled_text)


def parse_arguments():
    """Configura e parseia os argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description='Obtém e filtra logs de pods Kubernetes',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--pod',
        help='Nome do pod Kubernetes (use com --use-regex para padrão regex)'
    )
    group.add_argument(
        '--selector',
        help='Selector de labels do pod (ex: "app=nginx")'
    )

    parser.add_argument(
        '--namespace',
        required=True,
        help='Namespace Kubernetes'
    )
    parser.add_argument(
        '--use-regex',
        action='store_true',
        help='Interpretar --pod como regex'
    )
    parser.add_argument(
        '--grep-pattern',
        default=None,
        help='Padrões para filtrar logs (separados por ponto-e-vírgula)'
    )
    parser.add_argument(
        '--tail',
        type=int,
        default=100,
        help='Número de linhas de log para retornar'
    )
    parser.add_argument(
        '--context',
        type=int,
        default=2,
        dest='grep_around',
        help='Número de linhas de contexto ao redor dos erros'
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    try:
        # Obtém o nome do pod
        if args.selector:
            pod_name, identifier = get_k8s_pod_name(args.namespace, selector=args.selector)
        else:
            pod_name, identifier = get_k8s_pod_name(
                args.namespace,
                pod_regex=args.pod if args.use_regex else None
            )

        # Obtém os logs
        logs = get_k8s_logs(args.namespace, pod_name, args.tail)

        if args.grep_pattern is not None:
            # Filtra os logs
            filtered_logs = smart_error_grep(
                logs,
                args.grep_pattern.split(';'),
                grep_around=args.grep_around
            )
        else:
            filtered_logs = logs

        # Imprime formatado
        print_styled_logs(
            title=f"[bold]LOGS - {args.namespace}/{pod_name} ({identifier})[/]",
            filtered_logs=filtered_logs,
            color="red3",
            width=None
        )

    except Exception as e:
        print_styled_logs(
            title="[bold]ERRO[/]",
            filtered_logs=str(e),
            color="red",
            width=90
        )
        exit(1)

# # Usando selector
# python kubectl_cmd.py \
#   --namespace production \
#   --selector "app=rabbitmq" \
#   --grep-pattern "ERROR|WARN" \
#   --tail 50
#
# # Usando regex
# python kubectl_cmd.py \
#   --namespace staging \
#   --pod "nginx-\d+" \
#   --use-regex \
#   --grep-pattern "500" \
#   --context 1
if __name__ == "__main__":
    main()