// frontend/js/gestionar_miembros.js

document.addEventListener('DOMContentLoaded', () => {
    // --- Selección de Elementos del DOM ---
    const tablaMiembrosBody = document.getElementById('tablaMiembrosBody');
    const noDataMessage = document.getElementById('noDataMessage');
    const editMemberForm = document.getElementById('editMemberForm');
    const btnUpdateMember = document.getElementById('btnUpdateMember');
    const deleteMemberIdInput = document.getElementById('deleteMemberId');
    const confirmDeleteButton = document.getElementById('confirmDeleteButton');
    const generatedQrImage = document.getElementById('generatedQrImage');
    const qrImagePath = document.getElementById('qrImagePath');
    const btnEntrenarModelo = document.getElementById('btnEntrenarModelo');

    let currentMembers = [];

    // --- Definición de Funciones ---

    async function cargarMiembros() {
        try {
            showToast('Cargando miembros...', 'info', 1500);
            currentMembers = await obtenerMiembros();
            renderTable(currentMembers);
        } catch (error) {
            console.error("Error en cargarMiembros:", error);
            showToast(`Error al cargar miembros: ${error.message}`, 'error');
            if(tablaMiembrosBody) tablaMiembrosBody.innerHTML = '';
            if(noDataMessage) {
                noDataMessage.classList.remove('hidden');
                noDataMessage.textContent = 'Error al cargar datos. Revise la consola para más detalles.';
            }
        }
    }

    function renderTable(members) {
        if (!tablaMiembrosBody) {
            console.error("El elemento 'tablaMiembrosBody' no fue encontrado.");
            return;
        }
        tablaMiembrosBody.innerHTML = ''; 
        if (!members || members.length === 0) {
            if(noDataMessage) {
                noDataMessage.classList.remove('hidden');
                noDataMessage.textContent = 'No hay miembros registrados.';
            }
            return;
        }
        if(noDataMessage) noDataMessage.classList.add('hidden');

        members.forEach(member => {
            const row = tablaMiembrosBody.insertRow();
            row.innerHTML = `
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">${member.id}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">${member.nombre} ${member.apellido}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">${member.telefono || 'N/A'}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">${member.correo || 'N/A'}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${member.estado_membresia === 'activa' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                        ${member.estado_membresia}
                    </span>
                </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700 space-x-1 flex items-center">
                    <button onclick="window.abrirModalEditar(${member.id})" class="px-2 py-1 text-xs font-medium rounded-md bg-yellow-400 hover:bg-yellow-500 text-yellow-800" title="Editar Miembro">Editar</button>
                    <button onclick="window.abrirModalEliminar(${member.id})" class="px-2 py-1 text-xs font-medium rounded-md bg-red-500 hover:bg-red-600 text-white" title="Eliminar Miembro">Eliminar</button>
                    <button onclick="window.handleEnrolarRostro(${member.id}, '${member.nombre} ${member.apellido}')" class="px-2 py-1 text-xs font-medium rounded-md bg-purple-500 hover:bg-purple-600 text-white" title="Enrolar Rostro">Enrolar</button>
                    <button onclick="window.handleGenerarQR(${member.id}, this)" class="px-2 py-1 text-xs font-medium rounded-md bg-blue-500 hover:bg-blue-600 text-white" title="Generar y Guardar QR">Gen. QR</button> 
                    <button onclick="window.handleEnviarQRGuardado(${member.id}, this)" class="px-2 py-1 text-xs font-medium rounded-md bg-teal-500 hover:bg-teal-600 text-white" title="Enviar QR por WhatsApp">Enviar QR</button> 
                </td>
            `;
        });
    }
    
    window.handleEnrolarRostro = function(miembroId, nombreMiembro) {
        window.location.href = `registro_facial.html?miembroId=${miembroId}&nombre=${encodeURIComponent(nombreMiembro)}`;
    }

    window.abrirModalEditar = function(memberId) {
        const member = currentMembers.find(m => m.id === memberId);
        if (!member) { showToast("Miembro no encontrado.", "error"); return; }
        
        const form = document.getElementById('editMemberForm');
        if (!form) { console.error("Formulario de edición no encontrado."); return; }

        form.querySelector('#editMemberId').value = member.id;
        form.querySelector('#editNombre').value = member.nombre;
        form.querySelector('#editApellido').value = member.apellido;
        form.querySelector('#editTelefono').value = member.telefono || '';
        form.querySelector('#editCorreo').value = member.correo || ''; 
        form.querySelector('#editContrasenaMiembro').value = ''; 
        form.querySelector('#editFechaVencimiento').value = member.fechaVencimiento || '';
        form.querySelector('#editDuracionMembresia').value = ""; 
        openModal('editMemberModal');
    }

    window.abrirModalEliminar = function(memberId) { 
        if (deleteMemberIdInput) {
            deleteMemberIdInput.value = memberId;
            openModal('deleteConfirmModal');
        } else {
            console.error("El elemento con ID 'deleteMemberId' no fue encontrado en el DOM.");
            showToast("Error: No se pudo abrir el modal de confirmación.", "error");
        }
    }

    window.handleGenerarQR = async function(miembroId, buttonElement) {
        const originalText = buttonElement.textContent;
        buttonElement.disabled = true;
        buttonElement.textContent = '...';
        showToast(`Generando QR para miembro ID ${miembroId}...`, 'info', 2000);
        try {
            const response = await generarYGuardarQRMiembro(miembroId); 
            showToast(response.message || `QR generado y guardado.`, 'success', 4000);
            if (response.qr_image_url && generatedQrImage && qrImagePath) {
                const fullQrUrl = new URL(response.qr_image_url, window.location.origin).href;
                generatedQrImage.src = fullQrUrl;
                qrImagePath.textContent = `Guardado como: ${response.qr_filename || 'N/A'}`;
                openModal('qrImageModal');
            }
        } catch (error) {
            showToast(`Error al generar QR: ${error.message}`, 'error', 5000);
        } finally {
            buttonElement.disabled = false;
            buttonElement.textContent = originalText;
        }
    }

    window.handleEnviarQRGuardado = async function(miembroId, buttonElement) {
        const originalText = buttonElement.textContent;
        buttonElement.disabled = true;
        buttonElement.textContent = '...';
        showToast(`Solicitando envío de QR para miembro ID ${miembroId}...`, 'info', 3000);
        try {
            const response = await enviarQRMiembroGuardado(miembroId); 
            showToast(response.message || `Solicitud de envío de QR procesada.`, 'success', 5000);
        } catch (error) {
            showToast(`Error al enviar QR: ${error.message}`, 'error', 5000);
        } finally {
            buttonElement.disabled = false;
            buttonElement.textContent = originalText;
        }
    }

    // --- Asignación de Event Listeners ---

    editMemberForm?.addEventListener('submit', async function(event) {
        event.preventDefault();
        const memberId = document.getElementById('editMemberId').value;
        const formData = new FormData(this);
        const dataToUpdate = {};
        formData.forEach((value, key) => {
            if (key === 'contrasena' && !value) { return; }
            if (key !== 'memberId') {
                 if (value || key === 'telefono' || key === 'correo') { 
                    dataToUpdate[key] = value;
                }
            }
        });
        if (dataToUpdate.duracionMembresia === "") delete dataToUpdate.duracionMembresia;
        if (dataToUpdate.contrasena && dataToUpdate.contrasena.length < 6) {
            showToast("La nueva contraseña debe tener al menos 6 caracteres.", "error");
            return;
        }
        if (Object.keys(dataToUpdate).length === 0 && !(document.getElementById('editContrasenaMiembro').value)) { 
            showToast("No hay cambios para actualizar.", "info");
            closeModal('editMemberModal');
            return;
        }
        const btnUpdateMember = document.getElementById('btnUpdateMember');
        if (btnUpdateMember) { btnUpdateMember.disabled = true; btnUpdateMember.textContent = 'Actualizando...';}
        try {
            showToast('Actualizando miembro...', 'info', 2000);
            await actualizarMiembro(memberId, dataToUpdate);
            showToast('Miembro actualizado exitosamente.', 'success');
            closeModal('editMemberModal');
            resetForm('editMemberForm');
            cargarMiembros();
        } catch (error) { showToast(`Error al actualizar miembro: ${error.message}`, 'error', 4000);
        } finally { if (btnUpdateMember) { btnUpdateMember.disabled = false; btnUpdateMember.textContent = 'Actualizar'; } }
    });

    confirmDeleteButton?.addEventListener('click', async () => {
        const memberId = deleteMemberIdInput.value;
        const button = confirmDeleteButton;
        button.disabled = true; button.textContent = 'Eliminando...';
        try {
            showToast('Eliminando miembro...', 'info', 2000);
            await eliminarMiembro(memberId);
            showToast('Miembro eliminado exitosamente.', 'success');
            closeModal('deleteConfirmModal');
            cargarMiembros();
        } catch (error) { showToast(`Error al eliminar miembro: ${error.message}`, 'error', 4000);
        } finally { button.disabled = false; button.textContent = 'Aceptar'; }
    });

    btnEntrenarModelo?.addEventListener('click', async (event) => {
        const button = event.target;
        button.disabled = true;
        button.textContent = 'Entrenando...';
        showToast('Iniciando entrenamiento del modelo facial. Esto puede tardar.', 'info');
        try {
            const response = await entrenarModeloFacial();
            showToast(response.message, 'success', 5000);
        } catch (error) {
            showToast(`Error al entrenar modelo: ${error.message}`, 'error', 5000);
        } finally {
            button.disabled = false;
            button.textContent = 'Entrenar Modelo Facial';
        }
    });

    // --- Carga Inicial ---
    cargarMiembros();
});
