document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('.add-to-cart');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            alert('Блюдо добавлено в корзину!');
        });
    });
});
