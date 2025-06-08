// frontend/js/utils.js

/**
 * Muestra una notificación toast en pantalla.
 * @param {string} message - El mensaje a mostrar.
 * @param {string} type - El tipo de notificación ('success', 'error', 'info', 'warning'). Por defecto 'info'.
 * @param {number} duration - Duración en milisegundos antes de que desaparezca. Por defecto 3000.
 */
function showToast(message, type = 'info', duration = 3000) {
    let toastElement = document.getElementById('globalToast');
    if (!toastElement) {
        toastElement = document.createElement('div');
        toastElement.id = 'globalToast';
        toastElement.className = 'fixed bottom-5 right-5 p-4 rounded-md text-white shadow-lg transition-all duration-500 ease-in-out opacity-0 transform translate-y-3 z-50'; // Añadido transform
        document.body.appendChild(toastElement);
    }

    toastElement.textContent = message;
    
    toastElement.classList.remove('bg-green-500', 'bg-red-500', 'bg-blue-500', 'bg-yellow-500', 'bg-gray-700', 'opacity-100', 'opacity-0', 'translate-y-0', 'translate-y-3');
    void toastElement.offsetWidth; // Forzar reflow para reiniciar animación

    if (type === 'success') toastElement.classList.add('bg-green-500');
    else if (type === 'error') toastElement.classList.add('bg-red-500');
    else if (type === 'info') toastElement.classList.add('bg-blue-500');
    else if (type === 'warning') toastElement.classList.add('bg-yellow-500');
    else toastElement.classList.add('bg-gray-700');

    // Mostrar el toast con animación
    toastElement.classList.add('opacity-100', 'translate-y-0');
    toastElement.classList.remove('opacity-0', 'translate-y-3');


    // Ocultar después de la duración
    setTimeout(() => {
        toastElement.classList.remove('opacity-100', 'translate-y-0');
        toastElement.classList.add('opacity-0', 'translate-y-3');
    }, duration);
}

// Mantener showNotification por si se usa en otro lado, o se puede eliminar si showToast la reemplaza completamente.
function showNotification(message, type = 'info', duration = 3000) {
    const container = document.body; 
    const notification = document.createElement('div');
    notification.className = `notification ${type}`; 
    notification.textContent = message;
    container.appendChild(notification);
    void notification.offsetWidth; 
    notification.classList.add('show');
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 500); 
    }, duration);
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        if (modal.classList.contains('modal-global')) {
             modal.classList.add('flex');
        }
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        if (modal.classList.contains('modal-global')) {
            modal.classList.remove('flex');
        }
    }
}

function resetForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.reset();
    }
}

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
