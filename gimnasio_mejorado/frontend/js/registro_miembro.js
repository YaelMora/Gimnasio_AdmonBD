// frontend/js/registro_miembro.js

document.addEventListener('DOMContentLoaded', () => {
    // --- Selección de Elementos del DOM ---
    const formView = document.getElementById('formView');
    const facialEnrollmentView = document.getElementById('facialEnrollmentView');
    const registroMiembroForm = document.getElementById('registroMiembroForm');
    const membresiaSeleccionadaInput = document.getElementById('membresiaSeleccionada');
    const btnAbrirModalGerente = document.getElementById('btnAbrirModalGerente');
    const validateManagerForm = document.getElementById('validateManagerForm');
    
    // Elementos de la vista de enrolamiento facial
    const video = document.getElementById('webcamFeed');
    const startCameraButton = document.getElementById('startCameraButton');
    const capturePhotoButton = document.getElementById('capturePhotoButton');
    const finishEnrollmentButton = document.getElementById('finishEnrollmentButton');
    const photoCounterSpan = document.getElementById('photoCounter');
    const capturedPhotosPreview = document.getElementById('capturedPhotosPreview');

    // --- Variables de Estado ---
    let nuevoMiembroId = null;
    let nuevoMiembroNombre = '';
    let selectedMembershipButton = null;
    let stream = null;
    let fotosEnroladasCount = 0;
    const FOTOS_REQUERIDAS = 5; // Requerimiento actualizado a 5 fotos

    // --- Lógica de Selección de Membresía ---
    document.querySelectorAll('.membership-button').forEach(button => {
        button.addEventListener('click', function() {
            const duration = this.dataset.duration;
            
            if (selectedMembershipButton) {
                selectedMembershipButton.classList.remove('bg-blue-500', 'text-white', 'border-blue-500');
                selectedMembershipButton.classList.add('border-gray-300');
            }
            
            this.classList.add('bg-blue-500', 'text-white', 'border-blue-500');
            this.classList.remove('border-gray-300');
            
            if (membresiaSeleccionadaInput) {
                membresiaSeleccionadaInput.value = duration;
            }
            selectedMembershipButton = this;
        });
    });

    // --- Lógica de Cambio de Vista y Registro ---
    function switchToEnrollmentView() {
        console.log("[Registro] Llamando a switchToEnrollmentView().");
        const nameSpan = document.getElementById('enrollmentMemberName');
        const formV = document.getElementById('formView');
        const facialV = document.getElementById('facialEnrollmentView');

        if (nameSpan) nameSpan.textContent = nuevoMiembroNombre;
        if (formV) formV.classList.add('hidden');
        if (facialV) facialV.classList.remove('hidden');
        if (capturePhotoButton) capturePhotoButton.textContent = `Capturar Foto (${fotosEnroladasCount} / ${FOTOS_REQUERIDAS})`;
        console.log("[Registro] Clases de visibilidad actualizadas.");
    }

    if(registroMiembroForm) {
        registroMiembroForm.addEventListener('submit', (e) => e.preventDefault()); 
    }
    
    btnAbrirModalGerente?.addEventListener('click', () => {
        const contrasena = document.getElementById('contrasenaMiembro').value;
        if (!registroMiembroForm.checkValidity()) {
            registroMiembroForm.reportValidity();
            return;
        }
        if (contrasena !== document.getElementById('confirmarContrasenaMiembro').value) {
            showToast("Las contraseñas del miembro no coinciden.", "error");
            return;
        }
        if(contrasena.length < 6) {
            showToast("La contraseña del miembro debe tener al menos 6 caracteres.", "error");
            return;
        }
        if(!membresiaSeleccionadaInput.value) {
            showToast("Por favor, seleccione una membresía.", "error");
            return;
        }
        openModal('validateManagerModal');
    });

    validateManagerForm?.addEventListener('submit', async function(event) {
        event.preventDefault();
        const btnConfirm = document.getElementById('btnConfirmValidateManager');
        btnConfirm.disabled = true;
        btnConfirm.textContent = 'Procesando...';
        try {
            const miembroData = getFormData('registroMiembroForm');
            delete miembroData.confirmarContrasenaMiembro;
            
            const dataParaRegistrar = { 
                ...miembroData, 
                gerenteId: document.getElementById('idGerente').value, 
                contrasenaGerente: document.getElementById('contrasenaGerente').value 
            };
            
            const nuevoMiembro = await registrarMiembro(dataParaRegistrar);
            console.log("[Registro] Respuesta del servidor:", nuevoMiembro);
            
            if (nuevoMiembro && nuevoMiembro.id) {
                nuevoMiembroId = nuevoMiembro.id;
                nuevoMiembroNombre = nuevoMiembro.nombre;
                
                showToast(`Miembro ${nuevoMiembroNombre} (ID: ${nuevoMiembroId}) registrado. Procediendo...`, 'success', 4000);
                closeModal('validateManagerModal');

                console.log("[Registro] Llamando a switchToEnrollmentView() en 500ms.");
                setTimeout(() => switchToEnrollmentView(), 500);
            } else {
                console.error("[Registro] La respuesta del servidor no contenía un ID de miembro válido.", nuevoMiembro);
                showToast("Error: No se recibió confirmación del registro del miembro.", "error");
            }

        } catch (error) {
            showToast(`Error: ${error.message}`, 'error', 5000);
        } finally {
            btnConfirm.disabled = false;
            btnConfirm.textContent = 'Confirmar Registro';
        }
    });

    // --- Lógica de la Cámara para Enrolamiento ---
    startCameraButton?.addEventListener('click', async () => {
        if (stream && stream.active) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
            if(video) video.srcObject = null;
            if(capturePhotoButton) capturePhotoButton.disabled = true;
            if(startCameraButton) startCameraButton.textContent = 'Iniciar Cámara';
            showToast('Cámara detenida.');
        } else {
            try {
                stream = await navigator.mediaDevices.getUserMedia({ video: true });
                if(video) video.srcObject = stream;
                if(capturePhotoButton) capturePhotoButton.disabled = false;
                if(startCameraButton) startCameraButton.textContent = 'Detener Cámara';
                showToast('Cámara iniciada.', 'info');
            } catch (error) { showToast('No se pudo acceder a la cámara.', 'error'); }
        }
    });

    capturePhotoButton?.addEventListener('click', async () => {
        if (!stream || !stream.active || !nuevoMiembroId) {
            showToast('Inicie la cámara y asegúrese de que el miembro esté registrado primero.', 'error');
            return;
        }
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(async (blob) => {
            if (!blob) { showToast('Error al capturar la imagen.', 'error'); return; }
            capturePhotoButton.disabled = true;
            capturePhotoButton.textContent = 'Procesando...';
            try {
                showToast('Enviando foto para enrolamiento...', 'info');
                // Llama a la función de api.js que usa el endpoint de OpenCV
                const response = await enrolarRostroMiembro(nuevoMiembroId, blob);
                showToast(response.message, 'success');
                
                fotosEnroladasCount++;
                if(photoCounterSpan) photoCounterSpan.textContent = fotosEnroladasCount;
                
                const imgPreview = document.createElement('img');
                imgPreview.src = URL.createObjectURL(blob);
                imgPreview.className = 'w-full h-auto object-cover rounded-md shadow-sm';
                if(capturedPhotosPreview) capturedPhotosPreview.appendChild(imgPreview);

            } catch (error) {
                showToast(`Error al enrolar foto: ${error.message}`, 'error');
            } finally {
                capturePhotoButton.disabled = false;
                capturePhotoButton.textContent = `Capturar Foto (${fotosEnroladasCount} / ${FOTOS_REQUERIDAS})`;
            }
        }, 'image/jpeg');
    });
    
    finishEnrollmentButton?.addEventListener('click', async () => {
        if (fotosEnroladasCount < FOTOS_REQUERIDAS) {
            showToast(`Debe tomar al menos ${FOTOS_REQUERIDAS} fotos. Faltan ${FOTOS_REQUERIDAS - fotosEnroladasCount}.`, 'warning', 4000);
            return;
        }
        showToast('Finalizando... Entrenando modelo de reconocimiento.', 'info', 4000);
        finishEnrollmentButton.disabled = true;
        finishEnrollmentButton.textContent = 'Entrenando...';
        try {
            const response = await entrenarModeloFacial();
            showToast(response.message, 'success', 5000);
            setTimeout(() => {
                window.location.href = 'gestionar_miembros.html';
            }, 5000);
        } catch(error) {
            showToast(`Error al entrenar modelo: ${error.message}`, 'error', 5000);
            finishEnrollmentButton.disabled = false;
            finishEnrollmentButton.textContent = 'Finalizar y Entrenar Modelo';
        }
    });
});
