// --- FUNCIONES DINÁMICAS PARA LA TIENDA DE FAJAS ISABELLA ---

async function abrirModalProductoDinamico(productoId) {
    const contenedorModal = document.getElementById("modal-contenido-dinamico");
    const modalElemento = document.getElementById("miModalProducto");

    if (!contenedorModal || !modalElemento) {
        console.error("No se encontraron los elementos del modal en el DOM.");
        return;
    }

    try {
        // 1. Mostrar estado de carga rápido
        contenedorModal.innerHTML = `
            <div class="text-center py-6">
                <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-rose-600"></div>
                <p class="text-xs text-slate-500 mt-2 font-medium">Consultando stock y precios en tiempo real...</p>
            </div>
        `;
        modalElemento.style.display = "block";

        // 2. Consulta en vivo al backend (FastAPI)
        const response = await fetch(`/web/producto/${productoId}`);
        const data = await response.json();

        if (data.status !== "success" || !data.variantes || data.variantes.length === 0) {
            contenedorModal.innerHTML = `
                <div class="text-center py-6">
                    <p class="text-rose-600 font-bold text-sm">⚠️ Agotado temporalmente</p>
                    <p class="text-xs text-slate-500 mt-1">Esta prenda se acaba de vender. ¡Regresa pronto!</p>
                </div>
            `;
            return;
        }

        // 3. Renderizar las variantes disponibles con precio y stock al segundo
        let htmlVariantes = '<div class="grid grid-cols-2 gap-3 mt-3">';
        
        data.variantes.forEach(v => {
            htmlVariantes += `
                <div class="border border-slate-200 p-3 rounded-lg shadow-sm flex flex-col items-center justify-between bg-white hover:border-rose-300 transition">
                    <div class="text-center">
                        <span class="block text-xs font-bold text-slate-700 uppercase tracking-wide">Talla: ${v.talla}</span>
                        <span class="block text-xs text-slate-500">Color: ${v.color}</span>
                    </div>
                    
                    <div class="my-2 text-center">
                        <span class="block text-base font-extrabold text-rose-600">$${v.precio.toFixed(2)}</span>
                        <span class="inline-block text-[10px] font-semibold bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full mt-1 border border-emerald-200">
                            ${v.stock} disp.
                        </span>
                    </div>

                    <button onclick="agregarAlCarrito(${v.id}, '${data.nombre}', '${v.talla}', '${v.color}', ${v.precio})" 
                            class="w-full bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold py-1.5 px-2 rounded-md shadow-sm transition active:scale-95">
                        Seleccionar
                    </button>
                </div>
            `;
        });
        
        htmlVariantes += '</div>';

        // 4. Inyectar datos en el modal
        contenedorModal.innerHTML = htmlVariantes;

    } catch (error) {
        console.error("Error al obtener disponibilidad en tiempo real:", error);
        contenedorModal.innerHTML = `
            <p class="text-center text-xs text-red-500 py-4">Error al consultar precios y stock. Inténtalo de nuevo.</p>
        `;
    }
}

// Función para cerrar el modal (asegúrate de que coincida con tu botón de cerrar en el HTML)
function cerrarModalProducto() {
    const modalElemento = document.getElementById("miModalProducto");
    if (modalElemento) {
        modalElemento.style.display = "none";
    }
}