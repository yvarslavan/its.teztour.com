document.addEventListener('DOMContentLoaded', function() {
    // Обработка клика по элементам подменю
    document.querySelectorAll('.dropdown-submenu a.dropdown-toggle').forEach(function(element) {
        element.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            let subMenu = this.nextElementSibling;
            let allSubMenus = document.querySelectorAll('.dropdown-submenu .dropdown-menu');

            allSubMenus.forEach(function(menu) {
                if (menu !== subMenu) {
                    menu.style.display = 'none';
                }
            });

            subMenu.style.display = subMenu.style.display === 'block' ? 'none' : 'block';
        });
    });
});
