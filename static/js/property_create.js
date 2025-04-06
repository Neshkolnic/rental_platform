document.addEventListener('DOMContentLoaded', function() {
    // Инициализация карты
    ymaps.ready(function() {
        const map = new ymaps.Map('map', {
            center: [55.75, 37.61],
            zoom: 10
        });

        const addressInput = document.querySelector('#id_address');

        addressInput.addEventListener('change', function() {
            ymaps.geocode(this.value).then(function(res) {
                const firstGeoObject = res.geoObjects.get(0);
                if (firstGeoObject) {
                    map.geoObjects.removeAll();
                    map.geoObjects.add(firstGeoObject);
                    map.setCenter(firstGeoObject.geometry.getCoordinates());

                    document.getElementById('id_latitude').value = firstGeoObject.geometry.getCoordinates()[0];
                    document.getElementById('id_longitude').value = firstGeoObject.geometry.getCoordinates()[1];
                }
            });
        });
    });

    // Обработка загрузки фотографий
    const photoInput = document.getElementById('id_photos');
    const previewContainer = document.getElementById('photo-preview');

    photoInput.addEventListener('change', function() {
        previewContainer.innerHTML = '';

        if (this.files.length > 17) {
            alert(`Максимум можно загрузить 17 фотографий. Вы выбрали ${this.files.length}`);
            this.value = '';
            return;
        }

        Array.from(this.files).forEach((file, index) => {
            const reader = new FileReader();

            reader.onload = function(e) {
                const preview = document.createElement('div');
                preview.className = 'preview-item';
                preview.innerHTML = `
                    <img src="${e.target.result}" alt="Preview">
                    <span class="photo-number">${index + 1}</span>
                    ${index === 0 ? '<span class="primary-badge">Основное</span>' : ''}
                `;
                previewContainer.appendChild(preview);
            }

            reader.readAsDataURL(file);
        });
    });
});