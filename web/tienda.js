const API_URL = "/api/web/inventario";
const API_CATEGORIAS = "/api/web/categorias";
const SVG_FALLBACK = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'><rect width='100%' height='100%' fill='%23f1f5f9'/><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' fill='%2394a3b8' font-size='10'>Fajas Isabella</text></svg>";

let productos = [];
let productosFiltrados = [];
let categoriasOficiales = [];
let productoSeleccionado = null;
let tallaSeleccionada = "";
let colorSeleccionado = "";
let cantidadSeleccionada = 1;
let carrito = [];
let categoriaSeleccionadaActual = "TODAS";

async function inicializarTienda() {
    await cargarInventario();
    actualizarBotonCuentaNav();
}

async function cargarInventario() {
    try {
        const [resProductos, resCategorias] = await Promise.all([
            fetch(API_URL),
            fetch(API_CATEGORIAS)
        ]);

        if (resProductos.ok) {
            productos = await resProductos.json();
        } else {
            productos = [];
        }

        if (resCategorias.ok) {
            categoriasOficiales = await resCategorias.json();
        } else {
            categoriasOficiales = [];
        }
    } catch (e) {
        productos = [];
        categoriasOficiales = [];
    }

    productosFiltrados = [...productos];
    cargarCategoriasWeb();
    renderizarCatalogo();
}

function obtenerRutaImagenProducto(imagenUrl) {
    if (!imagenUrl || imagenUrl.trim() === "" || imagenUrl === "/logo.png" || imagenUrl === "logo.png") {
        return SVG_FALLBACK;
    }
    if (imagenUrl.startsWith("http://") || imagenUrl.startsWith("https://")) {
        return imagenUrl;
    }
    let nombreArchivo = imagenUrl.split('/').pop().trim();
    return `/img/${nombreArchivo}`;
}

function cargarCategoriasWeb() {
    const contenedor = document.getElementById("categorias-scroll");
    const dropdownContainer = document.getElementById("dropdown-categorias-dinamico");
    
    let htmlScroll = `
        <button onclick="filtrarCategoria('TODAS')" id="btn-cat-TODAS" class="btn-categoria flex flex-col items-center shrink-0 focus:outline-none">
            <div class="circle-cat w-14 h-14 rounded-full overflow-hidden border-2 border-rose-500 p-0.5 transition-all shadow-xs bg-rose-50 flex items-center justify-center">
                <img src="/img/cat-todas.jpg" onerror="this.onerror=null; this.src='${SVG_FALLBACK}'" class="w-full h-full object-cover rounded-full" alt="Todas">
            </div>
            <span class="text-[10px] font-bold text-rose-600 mt-1 uppercase tracking-tight label-cat">Todas</span>
        </button>
    `;

    let htmlDropdown = `
        <a href="#" onclick="filtrarCategoria('TODAS')" class="block px-4 py-2 hover:bg-rose-50 text-slate-700 hover:text-rose-600 font-medium">✨ Ver Todo el Catálogo</a>
        <div class="border-t border-slate-100 my-1"></div>
    `;

    categoriasOficiales.forEach(catObj => {
        const nombreCat = catObj.nombre || catObj.categoria;
        let imgCat = obtenerRutaImagenProducto(catObj.imagen_url);

        htmlScroll += `
            <button onclick="filtrarCategoria('${nombreCat}')" id="btn-cat-${nombreCat}" class="btn-categoria flex flex-col items-center shrink-0 focus:outline-none">
                <div class="circle-cat w-14 h-14 rounded-full overflow-hidden border-2 border-slate-200 p-0.5 transition-all shadow-xs bg-rose-50 flex items-center justify-center">
                    <img src="${imgCat}" onerror="this.onerror=null; this.src='${SVG_FALLBACK}'" class="w-full h-full object-cover rounded-full" alt="${nombreCat}">
                </div>
                <span class="text-[10px] font-bold text-slate-700 mt-1 uppercase tracking-tight label-cat">${nombreCat}</span>
            </button>
        `;

        htmlDropdown += `
            <a href="#" onclick="filtrarCategoria('${nombreCat}')" class="block px-4 py-2 hover:bg-rose-50 text-slate-700 hover:text-rose-600 font-medium">${nombreCat}</a>
        `;
    });

    contenedor.innerHTML = htmlScroll;
    if (dropdownContainer) {
        dropdownContainer.innerHTML = htmlDropdown;
    }
}

function generarHTMLTarjetaProducto(p) {
    const variantes = p.variantes || [];
    const descuento = Number(p.descuento_oferta || 0);
    
    let preciosTextoHtml = "";
    if (variantes.length > 0) {
        const preciosCalculados = variantes.map(v => {
            let precioV = Number(v.precio || 0);
            if ((p.en_oferta || p.en_liquidacion) && descuento > 0) {
                precioV = Math.max(0, precioV - descuento);
            }
            return precioV;
        });

        const precioMin = Math.min(...preciosCalculados);
        const precioMax = Math.max(...preciosCalculados);
        const precioMinOrig = Math.min(...variantes.map(v => Number(v.precio || 0)));
        const precioMaxOrig = Math.max(...variantes.map(v => Number(v.precio || 0)));

        if ((p.en_oferta || p.en_liquidacion) && descuento > 0) {
            if (precioMin === precioMax) {
                preciosTextoHtml = `
                    <div class="flex items-center gap-2">
                        <span class="text-xs text-slate-400 line-through">$${precioMinOrig.toFixed(2)}</span>
                        <span class="text-sm font-black text-rose-600">$${precioMin.toFixed(2)}</span>
                    </div>
                `;
            } else {
                preciosTextoHtml = `
                    <div class="flex items-center gap-1">
                        <span class="text-[10px] text-slate-400 line-through">$${precioMinOrig.toFixed(2)}</span>
                        <span class="text-sm font-black text-rose-600">$${precioMin.toFixed(2)} - $${precioMax.toFixed(2)}</span>
                    </div>
                `;
            }
        } else {
            if (precioMin === precioMax) {
                preciosTextoHtml = `<span class="text-sm font-black text-slate-900">$${precioMin.toFixed(2)}</span>`;
            } else {
                preciosTextoHtml = `<span class="text-sm font-black text-slate-900">$${precioMin.toFixed(2)} - $${precioMax.toFixed(2)}</span>`;
            }
        }
    } else {
        preciosTextoHtml = `<span class="text-sm font-black text-slate-900">$0.00</span>`;
    }

    const coloresUnicos = variantes.length > 0 ? [...new Set(variantes.map(v => v.color))].join(", ") : "Variados";

    let badgePromo = '';
    if (p.en_liquidacion) {
        badgePromo = `<span class="absolute top-2 left-2 bg-rose-600 text-white text-[9px] font-black px-2 py-0.5 rounded-full shadow-md animate-pulse">🔥 LIQUIDACIÓN</span>`;
    } else if (p.en_oferta) {
        const descTxt = descuento > 0 ? ` -$${descuento.toFixed(2)}` : '';
        badgePromo = `<span class="absolute top-2 left-2 bg-amber-500 text-white text-[9px] font-black px-2 py-0.5 rounded-full shadow-md">🏷️ OFERTA${descTxt}</span>`;
    } else if (p.es_nuevo) {
        badgePromo = `<span class="absolute top-2 left-2 bg-blue-600 text-white text-[9px] font-black px-2 py-0.5 rounded-full shadow-md">✨ NUEVO</span>`;
    }

    const imgSrc = obtenerRutaImagenProducto(p.imagen_url);

    return `
        <div class="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs hover:shadow-lg transition flex flex-col justify-between group">
            <div class="relative bg-slate-50 h-48 flex items-center justify-center p-3 overflow-hidden">
                ${badgePromo}
                <img src="${imgSrc}" onerror="this.onerror=null; this.src='${SVG_FALLBACK}'" class="h-full object-contain group-hover:scale-105 transition-all duration-300" alt="${p.nombre}">
                <span class="absolute top-2 right-2 bg-slate-900/80 text-white text-[9px] font-bold px-2 py-0.5 rounded-full backdrop-blur-xs">
                    ${variantes.length} Opciones
                </span>
            </div>

            <div class="p-3.5 flex-1 flex flex-col justify-between">
                <div>
                    <span class="text-[9px] font-bold text-rose-600 tracking-wider uppercase">${p.categoria}</span>
                    <h3 class="text-xs font-bold text-slate-800 line-clamp-1 mb-1">${p.nombre}</h3>
                    <p class="text-[10px] text-slate-500 mb-2">Colores: <span class="font-medium text-slate-700">${coloresUnicos}</span></p>
                </div>

                <div class="pt-2 border-t border-slate-100 flex items-center justify-between">
                    <div>
                        <span class="text-[9px] text-slate-400 block">${(p.en_liquidacion || p.en_oferta) ? 'Precio Oferta' : 'Precio'}</span>
                        ${preciosTextoHtml}
                    </div>
                    <button onclick="abrirModal(${p.id})" class="bg-slate-900 hover:bg-rose-600 text-white font-bold text-[11px] px-3 py-1.5 rounded-xl transition shadow-xs cursor-pointer">
                        Ver Tallas
                    </button>
                </div>
            </div>
        </div>
    `;
}

function renderizarCatalogo() {
    const container = document.getElementById("catalog-container");
    const contadorElem = document.getElementById("total-productos");
    if (contadorElem) {
        contadorElem.innerText = `${productosFiltrados.length} modelos`;
    }

    if (productosFiltrados.length === 0) {
        container.innerHTML = `<div class="col-span-full text-center py-12 text-slate-400 text-sm">No encontramos modelos en esta categoría.</div>`;
    } else {
        container.innerHTML = productosFiltrados.map(p => generarHTMLTarjetaProducto(p)).join('');
    }

    const contenedorSeccionesSecundarias = document.getElementById("secciones-secundarias-container");
    if (contenedorSeccionesSecundarias) {
        const productosNuevos = productos.filter(p => p.es_nuevo === true);
        const productosOfertas = productos.filter(p => p.en_oferta === true);

        let htmlSecundario = '';
        if (productosNuevos.length > 0) {
            htmlSecundario += `
                <div class="mt-16 pt-8 border-t border-slate-200">
                    <div class="flex items-center justify-between mb-6">
                        <div class="flex items-center gap-2">
                            <span class="bg-blue-100 text-blue-700 p-2 rounded-xl text-xs"><i class="fa-solid fa-wand-magic-sparkles"></i></span>
                            <h3 class="text-base font-extrabold text-slate-900">✨ Mira lo Nuevo de Fajas Isabella</h3>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                        ${productosNuevos.map(p => generarHTMLTarjetaProducto(p)).join('')}
                    </div>
                </div>
            `;
        }

        if (productosOfertas.length > 0) {
            htmlSecundario += `
                <div class="mt-12 pt-8 border-t border-slate-200">
                    <div class="flex items-center justify-between mb-6">
                        <div class="flex items-center gap-2">
                            <span class="bg-amber-100 text-amber-700 p-2 rounded-xl text-xs"><i class="fa-solid fa-tags"></i></span>
                            <h3 class="text-base font-extrabold text-slate-900">🏷️ ¡Aprovecha nuestras Ofertas Especiales!</h3>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                        ${productosOfertas.map(p => generarHTMLTarjetaProducto(p)).join('')}
                    </div>
                </div>
            `;
        }
        contenedorSeccionesSecundarias.innerHTML = htmlSecundario;
    }
}

function abrirModal(productoId) {
    productoSeleccionado = productos.find(p => p.id === productoId);
    if (!productoSeleccionado) return;

    const variantes = productoSeleccionado.variantes || [];
    const tallas = [...new Set(variantes.map(v => v.talla))];
    const colores = [...new Set(variantes.map(v => v.color))];

    tallaSeleccionada = tallas[0] || "S";
    colorSeleccionado = colores[0] || "Negro";
    cantidadSeleccionada = 1;

    const imgSrcModal = obtenerRutaImagenProducto(productoSeleccionado.imagen_url);
    const primerPrecio = variantes[0] ? variantes[0].precio : 0;
    const descuento = Number(productoSeleccionado.descuento_oferta || 0);
    const precioFinalModal = (productoSeleccionado.en_oferta || productoSeleccionado.en_liquidacion) && descuento > 0 
        ? Math.max(0, primerPrecio - descuento) 
        : primerPrecio;

    const contenido = `
        <div class="flex gap-4 items-start mb-4">
            <img src="${imgSrcModal}" onerror="this.onerror=null; this.src='${SVG_FALLBACK}'" class="w-20 h-20 object-contain rounded-2xl bg-slate-50 p-2 border border-slate-100 shrink-0">
            <div>
                <span class="text-[10px] font-bold text-rose-600 tracking-wider uppercase">${productoSeleccionado.categoria}</span>
                <h3 class="text-base font-extrabold text-slate-900 leading-snug">${productoSeleccionado.nombre}</h3>
                <p id="modal-precio" class="text-xl font-black text-rose-600 mt-1">$${precioFinalModal.toFixed(2)}</p>
            </div>
        </div>

        <div class="space-y-3.5 border-t border-slate-100 pt-3">
            <div>
                <label class="text-xs font-bold text-slate-800 block mb-1.5">Talla:</label>
                <div class="flex gap-2 flex-wrap" id="selector-tallas">
                    ${tallas.map((t, idx) => `
                        <button onclick="seleccionarTalla('${t}')" id="btn-talla-${t}" type="button"
                            class="btn-talla px-3.5 py-1.5 text-xs rounded-xl font-bold border ${idx === 0 ? 'bg-rose-600 text-white border-rose-600 shadow-xs' : 'bg-white text-slate-700 border-slate-300'} transition cursor-pointer">
                            ${t}
                        </button>
                    `).join('')}
                </div>
            </div>

            <div>
                <label class="text-xs font-bold text-slate-800 block mb-1.5">Color:</label>
                <div class="flex gap-2 flex-wrap" id="selector-colores">
                    ${colores.map((c, idx) => `
                        <button onclick="seleccionarColor('${c}')" id="btn-color-${c}" type="button"
                            class="btn-color px-3.5 py-1.5 text-xs rounded-xl font-bold border ${idx === 0 ? 'bg-slate-900 text-white border-slate-900 shadow-xs' : 'bg-white text-slate-700 border-slate-300'} transition cursor-pointer">
                            ${c}
                        </button>
                    `).join('')}
                </div>
            </div>

            <div class="bg-rose-50/60 border border-rose-100 p-3 rounded-2xl mt-3">
                <span class="text-[10px] font-bold text-rose-600 uppercase tracking-wider block mb-1">📋 Resumen de Selección:</span>
                <div class="text-xs text-slate-800 space-y-1.5">
                    <div class="flex justify-between">
                        <span class="text-slate-500">Variante:</span>
                        <span class="font-bold text-slate-900"><span id="resumen-talla">${tallaSeleccionada}</span> / <span id="resumen-color">${colorSeleccionado}</span></span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-slate-500">Disponibilidad:</span>
                        <span class="font-mono text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded" id="modal-stock">Consultando...</span>
                    </div>

                    <hr class="border-rose-200 my-2">

                    <div class="flex justify-between items-center pt-1">
                        <span class="text-slate-700 font-bold">Cantidad:</span>
                        <div class="flex items-center border border-slate-300 rounded-lg bg-white overflow-hidden shadow-2xs">
                            <button onclick="cambiarCantidadModal(-1)" type="button" class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-extrabold transition cursor-pointer">-</button>
                            <input id="modal-cantidad-input" type="number" value="1" min="1" class="w-10 text-center text-xs font-black border-none outline-none bg-transparent" readonly>
                            <button onclick="cambiarCantidadModal(1)" type="button" class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-extrabold transition cursor-pointer">+</button>
                        </div>
                    </div>

                    <div class="flex justify-between items-center pt-1 text-sm font-black text-slate-900">
                        <span>Total Selección:</span>
                        <span id="modal-total-seleccion" class="text-rose-600 text-base">$0.00</span>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-2 gap-2 mt-2">
                <button onclick="agregarAlCarrito(false)" type="button"
                    class="bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-xs py-3 rounded-xl flex items-center justify-center gap-1.5 transition cursor-pointer">
                    <i class="fa-solid fa-plus"></i>
                    <span>Seguir Comprando</span>
                </button>

                <button onclick="agregarAlCarrito(true)" type="button"
                    class="bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs py-3 rounded-xl flex items-center justify-center gap-1.5 shadow-md shadow-rose-600/20 transition cursor-pointer">
                    <i class="fa-solid fa-cart-shopping"></i>
                    <span>Ir al Carrito</span>
                </button>
            </div>
        </div>
    `;

    const modalContenido = document.getElementById("modal-contenido");
    const modalProducto = document.getElementById("modal-producto");
    
    if (modalContenido) modalContenido.innerHTML = contenido;
    if (modalProducto) modalProducto.classList.remove("hidden");
    
    actualizarDetalleVariante();
}

function cambiarCantidadModal(delta) {
    const variante = obtenerVarianteActual();
    const stockMax = variante ? variante.stock : 99;

    cantidadSeleccionada += delta;
    if (cantidadSeleccionada < 1) cantidadSeleccionada = 1;
    if (cantidadSeleccionada > stockMax && stockMax > 0) cantidadSeleccionada = stockMax;

    const inputElem = document.getElementById("modal-cantidad-input");
    if (inputElem) {
        inputElem.value = cantidadSeleccionada;
    }
    actualizarDetalleVariante();
}

function obtenerVarianteActual() {
    if (!productoSeleccionado || !productoSeleccionado.variantes) return null;
    return productoSeleccionado.variantes.find(v => v.talla === tallaSeleccionada && v.color === colorSeleccionado) 
        || productoSeleccionado.variantes.find(v => v.talla === tallaSeleccionada) 
        || productoSeleccionado.variantes[0];
}

function seleccionarTalla(talla) {
    tallaSeleccionada = talla;
    document.querySelectorAll(".btn-talla").forEach(b => {
        b.classList.remove("bg-rose-600", "text-white", "border-rose-600");
        b.classList.add("bg-white", "text-slate-700", "border-slate-300");
    });
    const btn = document.getElementById(`btn-talla-${talla}`);
    if (btn) {
        btn.classList.remove("bg-white", "text-slate-700", "border-slate-300");
        btn.classList.add("bg-rose-600", "text-white", "border-rose-600");
    }
    actualizarDetalleVariante();
}

function seleccionarColor(color) {
    colorSeleccionado = color;
    document.querySelectorAll(".btn-color").forEach(b => {
        b.classList.remove("bg-slate-900", "text-white", "border-slate-900");
        b.classList.add("bg-white", "text-slate-700", "border-slate-300");
    });
    const btn = document.getElementById(`btn-color-${color}`);
    if (btn) {
        btn.classList.remove("bg-white", "text-slate-700", "border-slate-300");
        btn.classList.add("bg-slate-900", "text-white", "border-slate-900");
    }
    actualizarDetalleVariante();
}

function actualizarDetalleVariante() {
    const variante = obtenerVarianteActual();

    if (variante && productoSeleccionado) {
        let precioUnitario = variante.precio;
        const descuento = Number(productoSeleccionado.descuento_oferta || 0);
        if ((productoSeleccionado.en_oferta || productoSeleccionado.en_liquidacion) && descuento > 0) {
            precioUnitario = Math.max(0, precioUnitario - descuento);
        }

        const totalLinea = precioUnitario * cantidadSeleccionada;
        document.getElementById("modal-precio").innerText = `$${precioUnitario.toFixed(2)}`;
        document.getElementById("resumen-talla").innerText = tallaSeleccionada;
        document.getElementById("resumen-color").innerText = colorSeleccionado;
        document.getElementById("modal-stock").innerText = `Stock: ${variante.stock} disp. (${variante.sku})`;
        
        const elemTotal = document.getElementById("modal-total-seleccion");
        if (elemTotal) {
            elemTotal.innerText = `$${totalLinea.toFixed(2)}`;
        }
    }
}

function cerrarModal() {
    document.getElementById("modal-producto").classList.add("hidden");
}

function scrollCategorias(distancia) {
    const contenedor = document.getElementById("categorias-scroll");
    if (contenedor) {
        contenedor.scrollBy({ left: distancia, behavior: 'smooth' });
    }
}

function filtrarCategoria(cat) {
    categoriaSeleccionadaActual = cat;

    if (cat === 'LIQUIDACION') {
        document.getElementById("titulo-categoria").innerText = "🔥 Productos en Liquidación";
        productosFiltrados = productos.filter(p => p.en_liquidacion === true);
    } else if (cat === 'OFERTAS') {
        document.getElementById("titulo-categoria").innerText = "🏷️ Productos en Oferta Especial";
        productosFiltrados = productos.filter(p => p.en_oferta === true);
    } else if (cat === 'NEW') {
        document.getElementById("titulo-categoria").innerText = "✨ Nuevos Modelos (New)";
        productosFiltrados = productos.filter(p => p.es_nuevo === true);
    } else {
        document.getElementById("titulo-categoria").innerText = cat === 'TODAS' ? 'Todas las Prendas Disponibles' : `Categoría: ${cat}`;
        if (cat === 'TODAS') {
            productosFiltrados = [...productos];
        } else {
            productosFiltrados = productos.filter(p => (p.categoria || '').toUpperCase() === cat.toUpperCase());
        }
    }
    renderizarCatalogo();
}

function buscarProducto() {
    const query = document.getElementById("input-busqueda").value.toLowerCase();
    productosFiltrados = productos.filter(p => 
        p.nombre.toLowerCase().includes(query) || 
        p.categoria.toLowerCase().includes(query) ||
        (p.variantes && p.variantes.some(v => v.sku.toLowerCase().includes(query)))
    );
    renderizarCatalogo();
}

function agregarAlCarrito(abrirCarritoDrawer = false) {
    const variante = obtenerVarianteActual();
    const cantAgregar = cantidadSeleccionada > 0 ? cantidadSeleccionada : 1;
    let precioFinalUnitario = variante.precio;
    const descuento = Number(productoSeleccionado.descuento_oferta || 0);
    if ((productoSeleccionado.en_oferta || productoSeleccionado.en_liquidacion) && descuento > 0) {
        precioFinalUnitario = Math.max(0, precioFinalUnitario - descuento);
    }

    const itemExistente = carrito.find(item => item.sku === variante.sku);
    if (itemExistente) {
        itemExistente.cantidad += cantAgregar;
    } else {
        carrito.push({
            nombre: productoSeleccionado.nombre,
            sku: variante.sku,
            talla: tallaSeleccionada,
            color: colorSeleccionado,
            precio: precioFinalUnitario,
            imagen_url: productoSeleccionado.imagen_url || SVG_FALLBACK,
            categoria: productoSeleccionado.categoria,
            cantidad: cantAgregar
        });
    }

    cerrarModal();
    actualizarCarritoUI();

    if (abrirCarritoDrawer) {
        toggleCarrito();
    }
}

function actualizarCarritoUI() {
    const count = carrito.reduce((acc, item) => acc + item.cantidad, 0);
    const total = carrito.reduce((acc, item) => acc + (item.precio * item.cantidad), 0);

    document.getElementById("cart-count").innerText = count;
    document.getElementById("carrito-total").innerText = `$${total.toFixed(2)}`;

    const container = document.getElementById("carrito-items");
    if (carrito.length === 0) {
        container.innerHTML = `<div class="text-center py-12 text-slate-400 text-xs">Tu carrito está vacío por el momento.</div>`;
        return;
    }

    container.innerHTML = carrito.map((item, index) => {
        const imgItem = obtenerRutaImagenProducto(item.imagen_url);
        return `
            <div class="flex items-center justify-between p-3 bg-slate-50 border border-slate-100 rounded-xl">
                <div class="flex items-center gap-3">
                    <img src="${imgItem}" onerror="this.onerror=null; this.src='${SVG_FALLBACK}'" class="w-12 h-12 object-contain rounded-lg bg-white p-1 border">
                    <div>
                        <h4 class="text-xs font-bold text-slate-800 line-clamp-1">${item.nombre}</h4>
                        <p class="text-[10px] text-slate-500">Talla: <b>${item.talla}</b> | Color: <b>${item.color}</b></p>
                        <span class="text-xs font-black text-rose-600">$${item.precio.toFixed(2)} x ${item.cantidad}</span>
                    </div>
                </div>
                <button onclick="eliminarDelCarrito(${index})" class="text-slate-400 hover:text-rose-600 text-xs p-1 cursor-pointer">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            </div>
        `;
    }).join('');
}

function eliminarDelCarrito(index) {
    carrito.splice(index, 1);
    actualizarCarritoUI();
}

function toggleCarrito() {
    const drawer = document.getElementById("drawer-carrito");
    drawer.classList.toggle("hidden");
}

function enviarPedidoFinalWhatsApp() {
    if (carrito.length === 0) {
        alert("Tu carrito está vacío. Agrega una prenda antes de enviar tu pedido.");
        return;
    }

    let detalleText = "";
    let total = 0;

    carrito.forEach((item, idx) => {
        const subtotal = item.precio * item.cantidad;
        total += subtotal;
        detalleText += `${idx + 1}. *${item.nombre}*%0A   - Talla: ${item.talla} | Color: ${item.color}%0A   - SKU: ${item.sku}%0A   - Cantidad: ${item.cantidad} x $${item.precio.toFixed(2)} = $${subtotal.toFixed(2)}%0A%0A`;
    });

    const mensaje = `¡Hola Fajas Isabella! 👋 Deseo realizar la compra de las siguientes prendas de mi carrito:%0A%0A${detalleText}💰 *Total a Pagar:* $${total.toFixed(2)}%0A%0A¿Me ayudan a confirmar el pedido y coordinar el envío?`;
    
    window.open(`https://wa.me/593983870398?text=${mensaje}`, '_blank');
}

function iniciarPagoPaymentez() {
    if (carrito.length === 0) {
        alert("Tu carrito está vacío.");
        return;
    }

    const payloadCompra = {
        items: carrito.map(item => ({
            sku: item.sku,
            cantidad: item.cantidad,
            precio_unitario: item.precio
        }))
    };

    fetch('/api/pagos/iniciar-paymentez', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payloadCompra)
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            if (data.checkout_url && data.checkout_url !== "#") {
                window.location.href = data.checkout_url;
            } else {
                alert(data.mensaje || "Pasarela configurada en modo simulación de pruebas exitosamente.");
            }
        } else {
            alert("Error al iniciar el pago: " + (data.detail || "Intente nuevamente."));
        }
    })
    .catch(err => {
        console.error("Error de red:", err);
        alert("No se pudo conectar con el servidor de pagos.");
    });
}

function obtenerUsuarioLogueado() {
    const userStr = localStorage.getItem('usuario_fajas');
    return userStr ? JSON.parse(userStr) : null;
}

function actualizarBotonCuentaNav() {
    const usuario = obtenerUsuarioLogueado();
    const nombreNav = document.getElementById('nombre-usuario-nav');
    if (usuario) {
        const primerNombre = usuario.nombre.split(' ')[0];
        nombreNav.innerText = primerNombre;
    } else {
        nombreNav.innerText = "Mi Cuenta";
    }
}

function gestionarClicCuenta() {
    const usuario = obtenerUsuarioLogueado();
    if (usuario) {
        abrirModalPerfil();
    } else {
        abrirModalAuth();
    }
}

function abrirModalAuth() {
    document.getElementById('modal-auth').classList.remove('hidden');
}

function cerrarModalAuth() {
    document.getElementById('modal-auth').classList.add('hidden');
}

function cambiarTabAuth(tipo) {
    const btnLogin = document.getElementById('tab-login-btn');
    const btnReg = document.getElementById('tab-registro-btn');
    const boxLogin = document.getElementById('form-login-container');
    const boxReg = document.getElementById('form-registro-container');

    if (tipo === 'login') {
        btnLogin.className = "flex-1 pb-2 font-bold text-sm text-rose-600 border-b-2 border-rose-600";
        btnReg.className = "flex-1 pb-2 font-bold text-sm text-slate-400";
        boxLogin.classList.remove('hidden');
        boxReg.classList.add('hidden');
    } else {
        btnReg.className = "flex-1 pb-2 font-bold text-sm text-rose-600 border-b-2 border-rose-600";
        btnLogin.className = "flex-1 pb-2 font-bold text-sm text-slate-400";
        boxReg.classList.remove('hidden');
        boxLogin.classList.add('hidden');
    }
}

function toggleVisibilidadPassword(inputId, iconId) {
    const input = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
    if (input.type === "password") {
        input.type = "text";
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
    } else {
        input.type = "password";
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
    }
}

async function ejecutarLogin(event) {
    event.preventDefault();
    const correo = document.getElementById('login-correo').value;
    const password = document.getElementById('login-password').value;

    try {
        const res = await fetch('/api/web/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ correo, password })
        });
        
        const data = await res.json();

        if (res.ok && data.status === 'success') {
            localStorage.setItem('usuario_fajas', JSON.stringify(data.cliente));
            cerrarModalAuth();
            actualizarBotonCuentaNav();
            alert(data.mensaje);
        } else {
            alert("Error [Server]: " + (data.detail || JSON.stringify(data)));
        }
    } catch (e) {
        alert("Error de conexión con el servidor: " + e.message);
    }
}

async function ejecutarRegistro(event) {
    event.preventDefault();

    const nombre = document.getElementById('reg-nombre').value;
    const correo = document.getElementById('reg-correo').value;
    const password = document.getElementById('reg-password').value;
    const passwordConfirm = document.getElementById('reg-password-confirm').value;
    const telefono = document.getElementById('reg-telefono').value;
    const direccion = document.getElementById('reg-direccion').value;

    if (password !== passwordConfirm) {
        alert("⚠️ Las contraseñas no coinciden. Por favor verifíquelas e intente nuevamente.");
        return;
    }

    try {
        const payload = { nombre, correo, password, telefono, direccion };

        const res = await fetch('/api/web/auth/registro', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const rawText = await res.text();
        let data;
        try {
            data = JSON.parse(rawText);
        } catch(errJson) {
            alert("Error 500 Servidor: " + rawText);
            return;
        }

        if (res.ok && data.status === 'success') {
            localStorage.setItem('usuario_fajas', JSON.stringify(data.cliente));
            cerrarModalAuth();
            actualizarBotonCuentaNav();
            alert(data.mensaje);
        } else {
            let errorMsg = data.detail || "Error al registrarse.";
            if (Array.isArray(errorMsg)) {
                errorMsg = errorMsg.map(err => `${err.loc.join('.')}: ${err.msg}`).join(', ');
            }
            alert("Error [Server]: " + errorMsg);
        }
    } catch (e) {
        alert("Error de conexión con el servidor: " + e.message);
    }
}

async function abrirModalPerfil() {
    const usuario = obtenerUsuarioLogueado();
    if (!usuario) return;

    document.getElementById('perfil-nombre').innerText = usuario.nombre;
    document.getElementById('perfil-correo').innerText = usuario.correo;
    document.getElementById('perfil-inicial').innerText = usuario.nombre.charAt(0).toUpperCase();
    document.getElementById('modal-perfil').classList.remove('hidden');

    const container = document.getElementById('historial-pedidos-container');
    container.innerHTML = `<div class="text-center py-8 text-slate-400 text-xs">Cargando tus pedidos...</div>`;

    try {
        const res = await fetch(`/api/web/auth/pedidos/${usuario.id}`);
        const pedidos = await res.json();

        if (pedidos.length === 0) {
            container.innerHTML = `<div class="text-center py-8 text-slate-400 text-xs">Aún no tienes compras registradas. ¡Anímate a estrenar!</div>`;
            return;
        }

        container.innerHTML = pedidos.map(p => `
            <div class="bg-slate-50 border border-slate-100 rounded-xl p-3 text-xs space-y-1">
                <div class="flex justify-between font-bold text-slate-900">
                    <span>Factura #${p.numero_factura}</span>
                    <span class="text-rose-600">$${p.total.toFixed(2)}</span>
                </div>
                <div class="flex justify-between text-slate-500 text-[11px]">
                    <span>Fecha: ${p.fecha}</span>
                    <span class="font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">${p.estado_despacho}</span>
                </div>
                <div class="pt-1 border-t border-slate-200 text-[11px] flex justify-between">
                    <span>Courier: <b>${p.courier}</b></span>
                    <span>Guía: <b>${p.numero_guia}</b></span>
                </div>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = `<div class="text-center py-8 text-rose-500 text-xs">Error al cargar el historial.</div>`;
    }
}

function cerrarModalPerfil() {
    document.getElementById('modal-perfil').classList.add('hidden');
}

function cerrarSesion() {
    localStorage.removeItem('usuario_fajas');
    cerrarModalPerfil();
    actualizarBotonCuentaNav();
    alert("Has cerrado sesión correctamente.");
}

inicializarTienda();