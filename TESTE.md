# Lista de Testes - Bot Volante Minho 2.0

## Comandos para Lojas

### ✅ /start
- [ ] Registar nova loja
- [ ] Verificar mensagem de boas-vindas
- [ ] Confirmar que loja já registada recebe menu

### ✅ /calendario
- [ ] Mostrar calendário visual
- [ ] Cores corretas (🟢🔴🟣🔵🟡)
- [ ] Navegação entre meses (◀️ ▶️)
- [ ] Botão fechar funciona

### ✅ /pedido
- [ ] Mostrar tipos de pedido (Apoio, Férias, Outros)
- [ ] Calendário visual aparece
- [ ] Seleção de data funciona
- [ ] Seleção de período funciona (Manhã, Tarde, Todo o dia)
- [ ] Campo observações funciona
- [ ] Pedido criado com sucesso
- [ ] Notificação enviada aos admins

### ✅ /pedido (Férias)
- [ ] Selecionar tipo "Férias"
- [ ] Calendário para data início
- [ ] Calendário para data fim
- [ ] Criar múltiplos pedidos (um por dia)
- [ ] Observações adicionadas
- [ ] Notificação aos admins

### ✅ /meus_pedidos
- [ ] Listar pedidos da loja
- [ ] Mostrar status correto (⏳ Pendente, ✅ Aprovado, ❌ Rejeitado)
- [ ] Informações completas (tipo, data, período)
- [ ] Limite de 10 pedidos mais recentes

### ✅ /minha_loja
- [ ] Mostrar nome da loja
- [ ] Mostrar ID do Telegram
- [ ] Estatísticas: total, pendentes, aprovados

### ✅ /menu
- [ ] Mostrar menu principal
- [ ] Listar comandos disponíveis

### ✅ /help
- [ ] Mostrar ajuda completa
- [ ] Explicação de como criar pedido
- [ ] Legenda do calendário
- [ ] Informação sobre férias

---

## Comandos para Administradores

### ✅ /pendentes
- [ ] Listar todos os pedidos pendentes
- [ ] Mostrar informações completas (loja, tipo, data, período, observações)
- [ ] Botões Aprovar/Rejeitar funcionam
- [ ] Mensagem quando não há pendentes

### ✅ Aprovar Pedido
- [ ] Atualizar status para "Aprovado"
- [ ] Notificar loja
- [ ] Gerar link Google Calendar
- [ ] Mostrar botão "Adicionar ao Calendário"

### ✅ Rejeitar Pedido
- [ ] Pedir motivo da rejeição
- [ ] Atualizar status para "Rejeitado"
- [ ] Notificar loja com motivo

### ✅ /estatisticas
- [ ] Total de pedidos
- [ ] Por status (Pendente, Aprovado, Rejeitado)
- [ ] Por tipo (Apoio, Férias, Outros)
- [ ] Por período (Manhã, Tarde, Todo o dia)
- [ ] Top 5 lojas com mais pedidos

### ✅ /agenda_semana
- [ ] Mostrar próximos 7 dias
- [ ] Listar pedidos aprovados por dia
- [ ] Mostrar dia da semana e data
- [ ] Indicar quando não há pedidos

---

## Funcionalidades Gerais

### ✅ Base de Dados
- [ ] Utilizadores registados corretamente
- [ ] Pedidos guardados com todas as informações
- [ ] Observações guardadas
- [ ] Status atualizados corretamente

### ✅ Notificações
- [ ] Admin recebe notificação de novo pedido
- [ ] Loja recebe notificação de aprovação
- [ ] Loja recebe notificação de rejeição com motivo

### ✅ Calendário Visual
- [ ] 🟢 Verde = Disponível
- [ ] 🔴 Vermelho = Ocupado todo o dia
- [ ] 🟣 Roxo = Manhã ocupada
- [ ] 🔵 Azul = Tarde ocupada
- [ ] 🟡 Amarelo = Pedido pendente
- [ ] Dias passados desativados

### ✅ Google Calendar
- [ ] Link gerado corretamente
- [ ] Título inclui tipo e período
- [ ] Data e hora corretas
- [ ] Descrição com informações da loja

---

## Testes de Integração

### ✅ Fluxo Completo: Pedido Normal
1. [ ] Loja cria pedido de Apoio
2. [ ] Admin recebe notificação
3. [ ] Admin aprova pedido
4. [ ] Loja recebe confirmação
5. [ ] Calendário atualizado com cor correta

### ✅ Fluxo Completo: Pedido de Férias
1. [ ] Loja cria pedido de Férias (3 dias)
2. [ ] Sistema cria 3 pedidos individuais
3. [ ] Admin recebe notificação
4. [ ] Admin aprova todos
5. [ ] Calendário mostra 3 dias ocupados

### ✅ Fluxo Completo: Rejeição
1. [ ] Loja cria pedido
2. [ ] Admin rejeita com motivo
3. [ ] Loja recebe notificação com motivo
4. [ ] Status atualizado na base de dados

---

## Notas de Teste

- **Administradores configurados:** ID 228613920, ID 615966323
- **Bot Token:** 8365753572:AAGiZrUoYxxfYlrRWZaIwNGkKiWQ_EzdX78
- **Base de Dados:** /home/ubuntu/hugo_bot/database/hugo_bot.db
