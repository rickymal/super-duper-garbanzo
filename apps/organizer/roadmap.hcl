config {
  theme = "dark"
  gantt {
    dateFormat = "DD"
    title = "Roadmap"
    excludes = ["weekends"]
    tickInterval = "1day"
    
    milestones = [
      {
        name = "Início do milestone"
        id = "start"
        date = "2024-12-24"
        duration = "0d"
      }
    ]
    
    sections = [
      {
        name = "Concurso"
        tasks = [
          { name = "prp", id = "s1", status = "active", dependsOn = "start", duration = "1d" },
          { name = "Estudar parte técnica", status = "active", duration = "5d" },
          { name = "Estudar português", duration = "6d" },
          { name = "Estudar matérias extras", duration = "5d" },
          { name = "Imprimir todo o conteúdo", duration = "3d" },
          { name = "Leitura no Kindle", duration = "5d" },
          { name = "Separar conteúdo em PDFs", duration = "5d" },
          { name = "Começar a estudar", duration = "15d" }
        ]
      },
      {
        name = "ASAP (main)"
        tasks = [
          { name = "prp", id = "s2", status = "active", dependsOn = "start", duration = "1d" },
          { name = "Fazer as tarefas", deadline = "2025-02-04" },
          { name = "Emitir nota", deadline = "2024-12-01" }
        ]
      }
    ]
  }
}
