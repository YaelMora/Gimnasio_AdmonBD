// frontend/js/api.js
const API_BASE_URL = 'http://localhost:5000/api'; 

async function request(endpoint, method = 'GET', data = null, headers = {}) {
    const config = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            ...headers,
        },
    };

    if (data && (method === 'POST' || method === 'PUT')) {
        config.body = JSON.stringify(data);
    }

    try {
        console.log(`[API Request] ${method} ${API_BASE_URL}${endpoint}`, data || '');
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        
        console.log(`[API Response Raw] Status: ${response.status}, OK: ${response.ok}`);
        response.headers.forEach((value, name) => {
            console.log(`[API Response Header] ${name}: ${value}`);
        });

        const contentDisposition = response.headers.get("content-disposition");
        console.log(`[API Response] Content-Disposition: ${contentDisposition}`);

        if (contentDisposition?.includes("attachment")) {
            console.log("[API Response] Detected attachment.");
            if (!response.ok) {
                console.error(`[API Error Attachment] Status: ${response.status}`);
                let errorData;
                try { errorData = await response.json(); } catch (e) { errorData = { message: response.statusText || "Error en la respuesta del archivo." }; }
                throw new Error(errorData.message);
            }
            console.log("[API Response] Returning raw response object for attachment.");
            return response; 
        }

        console.log("[API Response] Not an attachment or header not detected as such. Processing as JSON.");
        const responseData = await response.json().catch((e) => {
            console.error("[API Response] Failed to parse JSON, returning null for responseData.", e);
            return null; 
        });

        if (!response.ok) {
            const errorMessage = responseData?.message || `Error ${response.status} - ${response.statusText}`;
            console.error(`[API Error JSON] Status: ${response.status}, Message: ${errorMessage}`, responseData);
            throw new Error(errorMessage);
        }
        
        if (response.status === 204) { console.log("[API Response] Status 204, returning null."); return null; }
        console.log("[API Response] Returning JSON data:", responseData);
        return responseData; 
    } catch (error) {
        console.error(`[API Request Failed] ${method} ${endpoint}:`, error.message, error);
        throw new Error(error.message || "Error desconocido en la solicitud API."); 
    }
}

// --- Miembros ---
async function registrarMiembro(miembroDataConGerenteAuth) { return request('/miembros', 'POST', miembroDataConGerenteAuth); }
async function obtenerMiembros() { return request('/miembros'); }
async function actualizarMiembro(id, miembroData) { return request(`/miembros/${id}`, 'PUT', miembroData); }
async function eliminarMiembro(id) { return request(`/miembros/${id}`, 'DELETE'); }
async function validarAccesoMiembro(miembroId, contrasena) { return request(`/miembros/${miembroId}/validar_acceso`, 'POST', { contrasena });}

async function generarYGuardarQRMiembro(miembroId) { // Nueva función
    console.log(`[API Call] generarYGuardarQRMiembro para ID: ${miembroId}`);
    return request(`/miembros/${miembroId}/generar_qr`, 'POST');
}

async function enviarQRMiembroGuardado(miembroId) { // Nombre modificado para claridad
    console.log(`[API Call] enviarQRMiembroGuardado para ID: ${miembroId}`);
    return request(`/miembros/${miembroId}/enviar_qr`, 'POST');
}

async function subirImagenMiembro(miembroId, imageFile) { 
    const formData = new FormData();
    formData.append('image', imageFile, imageFile.name || 'member_image.jpg'); 
    formData.append('miembroId', miembroId);
    try {
        const response = await fetch(`${API_BASE_URL}/miembros/imagen`, { method: 'POST', body: formData });
        const responseData = await response.json().catch(() => null);
        if (!response.ok) {
            const errorMessage = responseData?.message || `Error ${response.status} subiendo imagen`;
            throw new Error(errorMessage);
        }
        return responseData;
    } catch (error) { console.error('Error subiendo imagen:', error); throw error; }
}

// --- Gerentes ---
async function validarGerente(idGerente, contrasena) { return request('/gerentes/validar', 'POST', { idGerente, contrasena }); }
async function registrarGerente(gerenteData) { return request('/gerentes', 'POST', gerenteData); }
async function obtenerGerentes() { return request('/gerentes'); }
async function actualizarGerente(id, gerenteData) { return request(`/gerentes/${id}`, 'PUT', gerenteData); }
async function eliminarGerente(id) { return request(`/gerentes/${id}`, 'DELETE'); }

// --- Acceso ---
async function registrarAcceso(accesoData) { return request('/acceso', 'POST', accesoData); }
async function obtenerReporteAcceso() { return request('/acceso/reporte'); }
async function descargarReporteAccesoExcel(filtrosConAuth) {
    try {
        console.log("[Descarga Excel] Solicitando reporte con:", filtrosConAuth);
        const response = await request('/acceso/reporte/descargar_excel', 'POST', filtrosConAuth);
        console.log("[Descarga Excel] Respuesta recibida de request():", response);
        console.log("[Descarga Excel] Tipo de respuesta:", typeof response, "Instancia de Response:", response instanceof Response);
        if (response instanceof Response && response.ok) {
            console.log("[Descarga Excel] Procesando respuesta como archivo.");
            const blob = await response.blob();
            const filenameHeader = response.headers.get("content-disposition");
            let filename = "reporte_acceso.xlsx"; 
            if (filenameHeader) {
                const parts = filenameHeader.split('filename=');
                if (parts.length > 1) { filename = parts[1].split(';')[0].replace(/"/g, ''); }
            }
            console.log("[Descarga Excel] Nombre de archivo:", filename);
            const link = document.createElement('a');
            link.href = window.URL.createObjectURL(blob);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(link.href);
            return { success: true, message: "Descarga iniciada." };
        } else {
            console.error("[Descarga Excel] La respuesta no fue un archivo válido o hubo un error:", response);
            let errorMessage = "Error desconocido al procesar la descarga.";
            if (response && typeof response.message === 'string') { errorMessage = response.message;
            } else if (response === null || typeof response === 'undefined') {
                 errorMessage = "La respuesta del servidor fue nula o indefinida antes de intentar parsear como JSON.";
            }
            throw new Error(errorMessage);
        }
    } catch (error) {
        console.error("[Descarga Excel] Error en la función descargarReporteAccesoExcel:", error);
        throw error; 
    }
}
