// Плавна прокрутка для навігації
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Обробка форми
const form = document.querySelector('.contact-form');
form.addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Тут можна додати код для відправки даних на сервер
    alert('Дякуємо за ваше повідомлення! Ми зв\'яжемося з вами найближчим часом.');
    form.reset();
}); 