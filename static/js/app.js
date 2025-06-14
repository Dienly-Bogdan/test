// static/js/admin.js

// Для подтверждения удаления блюда в админке
function confirmDeleteDish() {
    return confirm('Точно удалить это блюдо?');
}

// Для автообновления списка заказов (polling) — опционально
function autoRefreshOrders(intervalSeconds = 20) {
    setTimeout(function() {
        window.location.reload();
    }, intervalSeconds * 1000);
}

// Подсветка изменившихся заказов (если обновлять через ajax, можно реализовать diff)