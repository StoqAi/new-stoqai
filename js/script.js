document.addEventListener('DOMContentLoaded', function() {
    let selectedRow = null;
    let selectedCodigo = null;
    const rows = document.querySelectorAll('#produtos-tabela tr[data-codigo]');
    rows.forEach(row => {
        row.addEventListener('click', function(e) {
            // Evita conflito ao clicar em input ou botão dentro da célula
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'BUTTON') return;
            if (selectedRow === this) {
                this.classList.remove('selected-row');
                selectedRow = null;
                selectedCodigo = null;
            } else {
                if (selectedRow) selectedRow.classList.remove('selected-row');
                selectedRow = this;
                selectedCodigo = this.getAttribute('data-codigo');
                this.classList.add('selected-row');
            }
        });
    });
    document.getElementById('btn-gerenciar').onclick = function() {
        if (selectedCodigo) {
            // atualizarEstoqueUrl deve ser definida no template index.html
            window.location.href = atualizarEstoqueUrl.replace('0', selectedCodigo);
        } else {
            alert('Selecione um produto na tabela para gerenciar.');
        }
    };
});