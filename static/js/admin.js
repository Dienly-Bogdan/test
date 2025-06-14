// Пример: Подтверждение удаления блюда
document.querySelectorAll('.btn-danger').forEach(btn => {
    btn.addEventListener('click', function(e) {
        if (!confirm('Вы уверены, что хотите удалить это блюдо?')) {
            e.preventDefault();
        }
    });
});
