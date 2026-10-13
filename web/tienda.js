// --- MÓDULO JS EXTERNO: TIENDA FAJAS ISABELLA ---

async function abrirModalDinamico(productoId) {
    const modalElemento = document.getElementById("modal-producto");
    const contenedorModal = document.getElementById("modal-contenido");

    if (!modalElemento || !contenedorModal) return;

    // 1. Mostrar estado de carga en tiempo real dentro del modal
    contenedorModal.innerHTML = `
        <div class="text-center py-10">
            <i class="fa-solid fa-circle-notch fa-spin text-3xl text-rose-600 mb-3"></i>
            <p class="text-xs font-bold text-slate-600">Consultando stock y precios en tiempo real...</p>
        </div>
    `;
    modalElemento.classList.remove("hidden");

    try {
        // 2. Petición en vivo al endpoint de FastAPI
        const response = await fetch(`/web/producto/${productoId}`);
        const data = await response.json();

        if (data.status !== "success" || !data.variantes || data.variantes.length === 0) {
            contenedorModal.innerHTML = `
                <div class="text-center py-8">
                    <p class="text-rose-600 font-bold text-sm">⚠️ Agotado Temporalmente</p>
                    <p class="text-xs text-slate-500 mt-1">Este producto se acaba de agotar. ¡Vuelve pronto!</p>
                </div>
            `;
            return;
        }

        // Seleccionar por defecto la primera variante activa
        let tallaActual = data.variantes[0].talla;
        let colorActual = data.variantes[0].color;
        let varianteSeleccionada = data.variantes[0];

        const imgSrcModal = obtenerRutaImagenProducto(data.imagen_url);

        // 3. Construir la interfaz del modal con datos frescos del servidor
        contenedorModal.innerHTML = `
            <div class="flex gap-4 items-start mb-4">
                <img src="${imgSrcModal}" onerror="this.onerror=null; this.src='${SVG_FALLBACK}'" class="w-20 h-20 object-contain rounded-2xl bg-slate-50 p-2 border border-slate-100 shrink-0">
                <div>
                    <span class="text-[10px] font-bold text-rose-600 tracking-wider uppercase">${data.categoria}</span>
                    <h3 class="text-base font-extrabold text-slate-900 leading-snug">${data.nombre}</h3>
                    <p id="modal-precio" class="text-xl font-black text-rose-600 mt-1">$${varianteSeleccionada.precio.toFixed(2)}</p>
                </div>
            </div>

            <div class="space-y-3.5 border-t border-slate-100 pt-3">
                <div>
                    <label class="text-xs font-bold text-slate-800 block mb-1.5">Talla:</label>
                    <div class="flex gap-2 flex-wrap" id="selector-tallas">
                        ${[...new Set(data.variantes.map(v => v.talla))].map((t, idx) => `
                            <button onclick="cambiarTallaDinamica(${productoId}, '${t}')" id="btn-talla-${t}" 
                                class="btn-talla px-3.5 py-1.5 text-xs rounded-xl font-bold border ${idx === 0 ? 'bg-rose-600 text-white border-rose-600 shadow-xs' : 'bg-white text-slate-700 border-slate-300'} transition">
                                ${t}
                            </button>
                        `).join('')}
                    </div>
                </div>

                <div>
                    <label class="text-xs font-bold text-slate-800 block mb-1.5">Color:</label>
                    <div class="flex gap-2 flex-wrap" id="selector-colores">
                        ${[...new Set(data.variantes.map(v => v.color))].map((c, idx) => `
                            <button onclick="cambiarColorDinamico(${productoId}, '${c}')" id="btn-color-${c}" 
                                class="btn-color px-3.5 py-1.5 text-xs rounded-xl font-bold border ${idx === 0 ? 'bg-slate-900 text-white border-slate-900 shadow-xs' : 'bg-white text-slate-700 border-slate-300'} transition">
                                ${c}
                            </button>
                        `).join('')}
                    </div>
                </div>

                <div class="bg-rose-50/60 border border-rose-100 p-3 rounded-2xl mt-3">
                    <span class="text-[10px] font-bold text-rose-600 uppercase tracking-wider block mb-1">📋 Resumen en Tiempo Real:</span>
                    <div class="text-xs text-slate-800 space-y-1">
                        <div class="flex justify-between">
                            <span class="text-slate-500">Variante:</span>
                            <span class="font-bold text-slate-900"><span id="resumen-talla">${varianteSeleccionada.talla}</span> / <span id="resumen-color">${varianteSeleccionada.color}</span></span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-slate-500">Stock Actual:</span>
                            <span class="font-mono text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded" id="modal-stock">Stock: ${varianteSeleccionada.stock} disp.</span>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-2 mt-2">
                    <button onclick="agregarAlCarritoDinamico(${data.id}, false)" 
                        class="bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-xs py-3 rounded-xl flex items-center justify-center gap-1.5 transition">
                        <i class="fa-solid fa-plus"></i>
                        <span>Seguir Comprando</span>
                    </button>

                    <button onclick="agregarAlCarritoDinamico(${data.id}, true)" 
                        class="bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs py-3 rounded-xl flex items-center justify-center gap-1.5 shadow-md shadow-rose-600/20 transition">
                        <i class="fa-solid fa-cart-shopping"></i>
                        <span>Ir al Carrito</span>
                    </button>
                </div>
            </div>
        `;

        // Guardar referencia temporal en memoria global para el manejo de variantes
        window.productoActivoDinamico = data;

    } catch (err) {
        console.error("Error al consultar producto dinámico:", err);
        contenedorModal.innerHTML = `<p class="text-center text-xs text-red-500 py-6">Error al obtener el stock en tiempo real.</p>`;
    }
}

function cambiarTallaDinamica(prodId, talla) {
    if (!window.productoActivoDinamico) return;
    
    document.querySelectorAll(".btn-talla").forEach(b => {
        b.classList.remove("bg-rose-600", "text-white", "border-rose-600");
        b.classList.add("bg-white", "text-slate-700", "border-slate-300");
    });
    const btn = document.getElementById(`btn-talla-${talla}`);
    if (btn) {
        btn.classList.remove("bg-white", "text-slate-700", "border-slate-300");
        btn.classList.add("bg-rose-600", "text-white", "border-rose-600");
    }

    const colorActual = document.getElementById("resumen-color").innerText;
    actualizarVistaVarianteActiva(talla, colorActual);
}

function cambiarColorDinamico(prodId, color) {
    if (!window.productoActivoDinamico) return;

    document.querySelectorAll(".btn-color").forEach(b => {
        b.classList.remove("bg-slate-900", "text-white", "border-slate-900");
        b.classList.add("bg-white", "text-slate-700", "border-slate-300");
    });
    const btn = document.getElementById(`btn-color-${color}`);
    if (btn) {
        btn.classList.remove("bg-white", "text-slate-700", "border-slate-300");
        btn.classList.add("bg-slate-900", "text-white", "border-slate-900");
    }

    const tallaActual = document.getElementById("resumen-talla").innerText;
    actualizarVistaVarianteActiva(tallaActual, color);
}

function actualizarVistaVarianteActiva(talla, color) {
    const data = window.productoActivoDinamico;
    if (!data) return;

    let variante = data.variantes.find(v => v.talla === talla && v.color === color) 
                || data.variantes.find(v => v.talla === talla) 
                || data.variantes[0];

    if (variante) {
        document.getElementById("modal-precio").innerText = `$${variante.precio.toFixed(2)}`;
        document.getElementById("resumen-talla").innerText = variante.talla;
        document.getElementById("resumen-color").innerText = variante.color;
        document.getElementById("modal-stock").innerText = `Stock: ${variante.stock} disp. (${variante.sku})`;
    }
}

function agregarAlCarritoDinamico(prodId, abrirDrawer = false) {
    const data = window.productoActivoDinamico;
    if (!data) return;

    const tallaActual = document.getElementById("resumen-talla").innerText;
    const colorActual = document.getElementById("resumen-color").innerText;

    let variante = data.variantes.find(v => v.talla === tallaActual && v.color === colorActual) || data.variantes[0];

    const itemExistente = carrito.find(item => item.sku === variante.sku);
    if (itemExistente) {
        itemExistente.cantidad += 1;
    } else {
        carrito.push({
            nombre: data.nombre,
            sku: variante.sku,
            talla: variante.talla,
            color: variante.color,
            precio: variante.precio,
            imagen_url: data.imagen_url || SVG_FALLBACK,
            categoria: data.categoria,
            cantidad: 1
        });
    }

    cerrarModal();
    actualizarCarritoUI();

    if (abrirDrawer) {
        toggleCarrito();
    }
}