// main.js

document.addEventListener('DOMContentLoaded', () => {
    loadMenuItems();
});

function loadMenuItems() {
    fetch('/api/menu')
        .then(res => res.json())
        .then(data => {
            const grid = document.querySelector('.menu-grid');
            grid.innerHTML = '';
            data.forEach(item => {
                const card = document.createElement('div');
                card.className = 'menu-item';
                card.innerHTML = `
                    <img src="${item.image_url}" alt="${item.name}">
                    <div class="info">
                        <h3>${item.name}</h3>
                        <p>${item.description}</p>
                        <div class="price">${item.price} ₽</div>
                        <button onclick="addToCart(${item.id})">Добавить в корзину</button>
                    </div>
                `;
                grid.appendChild(card);
            });
        });
}

function addToCart(id) {
    fetch('/api/cart/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: id })
    }).then(() => {
        alert('Товар добавлен в корзину!');
    });
}