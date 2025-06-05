// static/js/utils.js

/**
 * Muestra una notificación en pantalla.
 * @param {string} message - El mensaje a mostrar.
 * @param {string} type - El tipo de notificación ('success', 'error', 'info'). Por defecto 'info'.
 * @param {number} duration - Duración en milisegundos antes de que desaparezca. Por defecto 3000.
 */
function showNotification(message, type = 'info', duration = 3000) {
    const container = document.body;
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    container.appendChild(notification);

    // Forzar reflow para aplicar la transición inicial
    void notification.offsetWidth;

    notification.classList.add('show');

    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300); // Esperar a que termine la transición de salida
    }, duration);
}

/**
 * Abre un modal.
 * @param {string} modalId - El ID del elemento modal.
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex'); // O 'block' según tu diseño de modal
    }
}

/**
 * Cierra un modal.
 * @param {string} modalId - El ID del elemento modal.
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex'); // O 'block'
    }
}

/**
 * Limpia los campos de un formulario.
 * @param {string} formId - El ID del formulario.
 */
function resetForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.reset();
    }
}

/**
 * Obtiene los datos de un formulario como un objeto.
 * @param {string} formId - El ID del formulario.
 * @returns {object} - Objeto con los datos del formulario.
 */
function getFormData(formId) {
    const form = document.getElementById(formId);
    if (!form) return {};
    const formData = new FormData(form);
    const data = {};
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    return data;
}
