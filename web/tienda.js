// tienda.js - Carga dinámica del catálogo de Fajas Isabella
async function cargarSeccionInicio() {
    const container = document.getElementById('home-dinamico-container');
    if (!container) return;

    try {
        const res = await fetch('./home.html');
        if (res.ok) {
            const html = await res.text();
            container.innerHTML = html;
            container.style.display = 'block';
        } else {
            console.error("Error al cargar home.html: Estado", res.status);
        }
    } catch (err) {
        console.error("No se pudo cargar home.html", err);
    }

    if (typeof filtrarCategoria === 'function') {
        filtrarCategoria('TODAS');
    }
}

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
let whatsappUrlGlobal = "https://wa.me/593983870398";

async function inicializarTienda() {
    await cargarConfiguracionEmpresa();
    await cargarSeccionInicio();
    setTimeout(async () => {
        if (typeof window.inicializarHome === 'function') {
            window.inicializarHome();
        }
        await cargarInventario();
    }, 100);
    actualizarBotonCuentaNav();
}

async function cargarConfiguracionEmpresa() {
    try {
        const res = await fetch("/api/config/empresa");
        if (res.ok) {
            const data = await res.json();
            if (data.redes && data.redes.whatsapp) {
                whatsappUrlGlobal = data.redes.whatsapp;
            }
            if (data.redes) {
                if (document.getElementById("footer-instagram")) document.getElementById("footer-instagram").href = data.redes.instagram;
                if (document.getElementById("footer-facebook")) document.getElementById("footer-facebook").href = data.redes.facebook;
                if (document.getElementById("footer-tiktok")) document.getElementById("footer-tiktok").href = data.redes.tiktok;
                if (document.getElementById("footer-whatsapp")) document.getElementById("footer-whatsapp").href = data.redes.whatsapp;
            }
            if (document.getElementById("footer-direccion")) document.getElementById("footer-direccion").innerText = data.direccion || "";
            if (document.getElementById("footer-correo")) document.getElementById("footer-correo").innerText = data.correo || "";
        }
    } catch (e) {
        console.warn("No se pudo cargar la configuración de empresa.");
    }
}

async function cargarInventario() {
    const catalogContainer = document.getElementById('catalog-container');

    try {
        const [resProductos, resCategorias] = await Promise.allSettled([
            fetch(API_URL),
            fetch(API_CATEGORIAS)
        ]);

        if (resProductos.status === 'fulfilled' && resProductos.value.ok) {
            productos = await resProductos.value.json();
        } else {
            productos = [];
        }

        if (resCategorias.status === 'fulfilled' && resCategorias.value.ok) {
            categoriasOficiales = await resCategorias.value.json();
        } else {
            categoriasOficiales = [];
        }

    } catch (e) {
        console.error("Error al conectar:", e);
        productos = [];
        categoriasOficiales = [];
    }

    productosFiltrados = [...productos];
    
    cargarCategoriasWeb();
    renderizarCatalogo();
}

function obtenerRutaImagenProducto(imagenUrl) {
    if (!imagenUrl) return SVG_FALLBACK;
    
    // Convertir a string por seguridad y quitar espacios
    let urlLimpia = String(imagenUrl).trim();
    
    if (urlLimpia === "" || urlLimpia === "/logo.png" || urlLimpia === "logo.png") {
        return SVG_FALLBACK;
    }
    
    // Si contiene http o https, la retornamos obligatoriamente como URL absoluta entrecomillada/intacta
    if (urlLimpia.startsWith("http://") || urlLimpia.startsWith("https://")) {
        return urlLimpia;
    }
    
    // Si es una ruta local antigua
    let nombreArchivo = urlLimpia.split('/').pop().trim();
    return `/img/${nombreArchivo}`;
}

function cargarCategoriasWeb() {
    const contenedor = document.getElementById("categorias-scroll");
    const dropdownContainer = document.getElementById("dropdown-categorias-dinamico");
    if (!contenedor) return;
    
    let htmlScroll = `
        <button onclick="filtrarCategoria('TODAS')" id="btn-cat-TODAS" class="btn-categoria flex flex-col items-center shrink-0 focus:outline-none cursor-pointer">
            <div class="circle-cat w-14 h-14 rounded-full overflow-hidden border-2 border-rose-500 p-0.5 transition-all shadow-xs bg-rose-50 flex items-center justify-center">
                <img src="/img/cat-todas.jpg" onerror="this.onerror=null; this.src='${SVG_FALLBACK}'" class="w-full h-full object-cover rounded-full" alt="Todas">
            </div>
            <span class="text-[10px] font-bold text-rose-600 mt-1 uppercase tracking-tight label-cat">Todas</span>
        </button>
    `;

    let htmlDropdown = `
        <a href="#catalogo" onclick="filtrarCategoria('TODAS')" class="block px-4 py-2 hover:bg-rose-50 text-slate-700 hover:text-rose-600 font-medium">✨ Ver Todo el Catálogo</a>
        <div class="border-t border-slate-100 my-1"></div>
    `;

    if (Array.isArray(categoriasOficiales) && categoriasOficiales.length > 0) {
        categoriasOficiales.forEach(catObj => {
            const nombreCat = catObj.nombre || catObj.categoria;
            if (!nombreCat) return;

            // --- 🕵️‍♂️ CHIVATO DE CONSOLA WEB ---
            console.log(`[CHIVATO CATEGORIA] Nombre: "${nombreCat}" | imagen_url cruda:`, catObj.imagen_url);

            let imgCat = obtenerRutaImagenProducto(catObj.imagen_url);
            
            console.log(`[CHIVATO CATEGORIA] URL procesada final para "${nombreCat}":`, imgCat);

            htmlScroll += `
                <button onclick="filtrarCategoria('${nombreCat}')" id="btn-cat-${nombreCat}" class="btn-categoria flex flex-col items-center shrink-0 focus:outline-none cursor-pointer">
                    <div class="circle-cat w-14 h-14 rounded-full overflow-hidden border-2 border-slate-200 p-0.5 transition-all shadow-xs bg-rose-50 flex items-center justify-center">
                        <img src="${imgCat}" onerror="console.error('❌ Error cargando imagen para:', '${nombreCat}', 'SRC intentado:', this.src); this.onerror=null; this.src='${SVG_FALLBACK}';" class="w-full h-full object-cover rounded-full" alt="${nombreCat}">
                    </div>
                    <span class="text-[10px] font-bold text-slate-700 mt-1 uppercase tracking-tight label-cat">${nombreCat}</span>
                </button>
            `;

            htmlDropdown += `
                <a href="#catalogo" onclick="filtrarCategoria('${nombreCat}')" class="block px-4 py-2 hover:bg-rose-50 text-slate-700 hover:text-rose-600 font-medium">${nombreCat}</a>
            `;
        });
    }

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
            <div class="relative bg-slate-50 h-64 w-full flex items-center justify-center p-3 overflow-hidden">
                ${badgePromo}
                <img src="${imgSrc}" onerror="this.onerror=null; this.src='${SVG_FALLBACK}'" class="w-full h-full object-contain group-hover:scale-105 transition-all duration-300" alt="${p.nombre}">
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
                    <button onclick="abrirModal(${p.id})" class="bg-slate-900 hover:bg-rose-600 text-white font-bold text-[10px] px-2.5 py-1.5 rounded-xl transition shadow-xs cursor-pointer">
                        Ver Tallas y Colores
                    </button>
                </div>
            </div>
        </div>
    `;
}

function renderizarCatalogo() {
    const container = document.getElementById("catalog-container");
    const contadorElem = document.getElementById("total-productos");
    if (!container) return;

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
        let htmlSecundario = '';

        if (categoriaSeleccionadaActual !== 'TODAS') {
            const productosNuevos = productos.filter(p => p.es_nuevo === true);
            const productosOfertas = productos.filter(p => p.en_oferta === true);

            if (categoriaSeleccionadaActual !== 'NEW' && productosNuevos.length > 0) {
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

            if (categoriaSeleccionadaActual !== 'OFERTAS' && categoriaSeleccionadaActual !== 'LIQUIDACION' && productosOfertas.length > 0) {
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

    const varianteInicial = obtenerVarianteActual();
    const imgSrcModal = (varianteInicial && varianteInicial.imagen_url) 
        ? obtenerRutaImagenProducto(varianteInicial.imagen_url) 
        : obtenerRutaImagenProducto(productoSeleccionado.imagen_url);

    const primerPrecio = varianteInicial ? varianteInicial.precio : (variantes[0] ? variantes[0].precio : 0);
    const descuento = Number(productoSeleccionado.descuento_oferta || 0);
    const precioFinalModal = (productoSeleccionado.en_oferta || productoSeleccionado.en_liquidacion) && descuento > 0 
        ? Math.max(0, primerPrecio - descuento) 
        : primerPrecio;

    const contenido = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
            <div class="flex flex-col items-center justify-center bg-slate-50 rounded-2xl p-4 border border-slate-100 h-full min-h-[300px]">
                <img id="modal-imagen-producto" src="${imgSrcModal}" onerror="this.onerror=null; this.src='${SVG_FALLBACK}'" class="w-full h-72 object-contain rounded-xl transition-all duration-300">
            </div>

            <div class="flex flex-col justify-between space-y-3">
                <div>
                    <span class="text-[10px] font-bold text-rose-600 tracking-wider uppercase">${productoSeleccionado.categoria}</span>
                    <h3 class="text-base font-extrabold text-slate-900 leading-snug mb-1">${productoSeleccionado.nombre}</h3>
                    <p id="modal-precio" class="text-2xl font-black text-rose-600">$${precioFinalModal.toFixed(2)}</p>
                </div>

                <div class="space-y-3 border-t border-slate-100 pt-3">
                    <div>
                        <label class="text-xs font-bold text-slate-800 block mb-1">Talla:</label>
                        <div class="flex gap-2 flex-wrap" id="selector-tallas">
                            ${tallas.map((t, idx) => `
                                <button onclick="seleccionarTalla('${t}')" id="btn-talla-${t}" type="button"
                                    class="btn-talla px-3 py-1 text-xs rounded-xl font-bold border ${idx === 0 ? 'bg-rose-600 text-white border-rose-600 shadow-xs' : 'bg-white text-slate-700 border-slate-300'} transition cursor-pointer">
                                    ${t}
                                </button>
                            `).join('')}
                        </div>
                    </div>

                    <div>
                        <label class="text-xs font-bold text-slate-800 block mb-1">Color (Círculos Interactivos):</label>
                        <div class="flex gap-2 flex-wrap" id="selector-colores">
                            ${colores.map((c, idx) => {
                                let bgHex = "#1e293b";
                                const cLower = c.toLowerCase();
                                if (cLower.includes('beige') || cLower.includes('nude') || cLower.includes('arena')) bgHex = "#d4b293";
                                else if (cLower.includes('blanco')) bgHex = "#ffffff";
                                else if (cLower.includes('azul')) bgHex = "#2563eb";
                                else if (cLower.includes('vino') || cLower.includes('rojo')) bgHex = "#9f1239";
                                else if (cLower.includes('gris')) bgHex = "#64748b";

                                const esSeleccionado = idx === 0;
                                return `
                                    <button onclick="seleccionarColor('${c}')" id="btn-color-${c}" type="button"
                                        class="btn-color flex items-center gap-1.5 px-3 py-1 text-xs rounded-xl font-bold border ${esSeleccionado ? 'bg-slate-900 text-white border-slate-900 shadow-xs' : 'bg-white text-slate-700 border-slate-300'} transition cursor-pointer">
                                        <span class="w-3 h-3 rounded-full border border-slate-300 inline-block shadow-2xs" style="background-color: ${bgHex};"></span>
                                        <span>${c}</span>
                                    </button>
                                `;
                            }).join('')}
                        </div>
                    </div>

                    <div class="bg-rose-50/60 border border-rose-100 p-2.5 rounded-xl">
                        <span class="text-[10px] font-bold text-rose-600 uppercase tracking-wider block mb-1">📋 Resumen de Selección:</span>
                        <div class="text-xs text-slate-800 space-y-1">
                            <div class="flex justify-between">
                                <span class="text-slate-500">Variante:</span>
                                <span class="font-bold text-slate-900"><span id="resumen-talla">${tallaSeleccionada}</span> / <span id="resumen-color">${colorSeleccionado}</span></span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-slate-500">Disponibilidad:</span>
                                <span class="font-mono text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded" id="modal-stock">Consultando...</span>
                            </div>
                            <div class="flex justify-between items-center pt-1">
                                <span class="text-slate-700 font-bold">Cantidad:</span>
                                <div class="flex items-center border border-slate-300 rounded-lg bg-white overflow-hidden shadow-2xs">
                                    <button onclick="cambiarCantidadModal(-1)" type="button" class="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-extrabold transition cursor-pointer">-</button>
                                    <input id="modal-cantidad-input" type="number" value="1" min="1" class="w-8 text-center text-xs font-black border-none outline-none bg-transparent" readonly>
                                    <button onclick="cambiarCantidadModal(1)" type="button" class="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-extrabold transition cursor-pointer">+</button>
                                </div>
                            </div>
                            <div class="flex justify-between items-center pt-1 text-sm font-black text-slate-900 border-t border-rose-200/60 mt-1">
                                <span>Total Selección:</span>
                                <span id="modal-total-seleccion" class="text-rose-600 text-base">$0.00</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-2 pt-2">
                    <button onclick="agregarAlCarrito(false)" type="button"
                        class="bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-[11px] py-2.5 rounded-xl flex items-center justify-center gap-1.5 transition cursor-pointer">
                        <i class="fa-solid fa-plus"></i>
                        <span>Seguir Comprando</span>
                    </button>

                    <button onclick="agregarAlCarrito(true)" type="button"
                        class="bg-rose-600 hover:bg-rose-700 text-white font-bold text-[11px] py-2.5 rounded-xl flex items-center justify-center gap-1.5 shadow-md shadow-rose-600/20 transition cursor-pointer">
                        <i class="fa-solid fa-cart-shopping"></i>
                        <span>Ir al Carrito</span>
                    </button>
                </div>
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

    const variante = obtenerVarianteActual();
    const imgElem = document.getElementById("modal-imagen-producto");
    if (imgElem && productoSeleccionado) {
        if (variante && variante.imagen_url && variante.imagen_url.trim() !== "") {
            imgElem.src = obtenerRutaImagenProducto(variante.imagen_url);
        } else {
            imgElem.src = obtenerRutaImagenProducto(productoSeleccionado.imagen_url);
        }
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
    const modal = document.getElementById("modal-producto");
    if (modal) modal.classList.add("hidden");
}

function scrollCategorias(distancia) {
    const contenedor = document.getElementById("categorias-scroll");
    if (contenedor) {
        contenedor.scrollBy({ left: distancia, behavior: 'smooth' });
    }
}

function filtrarCategoria(cat) {
    categoriaSeleccionadaActual = cat;
    const tituloCatElem = document.getElementById("titulo-categoria");
    const introContainer = document.getElementById("secciones-intro-container");

    if (cat === 'TODAS') {
        if (introContainer) introContainer.style.display = 'block';
        if (tituloCatElem) tituloCatElem.innerText = "Todas las Prendas Disponibles";
        productosFiltrados = [...productos];
    } else {
        if (introContainer) introContainer.style.display = 'none';

        if (cat === 'LIQUIDACION') {
            if (tituloCatElem) tituloCatElem.innerText = "🔥 Productos en Liquidación";
            productosFiltrados = productos.filter(p => p.en_liquidacion === true);
        } else if (cat === 'OFERTAS') {
            if (tituloCatElem) tituloCatElem.innerText = "🏷️ Productos en Oferta Especial";
            productosFiltrados = productos.filter(p => p.en_oferta === true);
        } else if (cat === 'NEW') {
            if (tituloCatElem) tituloCatElem.innerText = "✨ Nuevos Modelos (New)";
            productosFiltrados = productos.filter(p => p.es_nuevo === true);
        } else {
            if (tituloCatElem) tituloCatElem.innerText = `Colección: ${cat}`;
            productosFiltrados = productos.filter(p => (p.categoria || '').toUpperCase().trim() === cat.toUpperCase().trim());
        }
    }

    renderizarCatalogo();

    const catalogElem = document.getElementById("catalogo") || document.getElementById("catalog-container");
    if (catalogElem) {
        catalogElem.scrollIntoView({ behavior: 'smooth' });
    }
}

function buscarProducto() {
    const inputBusqueda = document.getElementById("input-busqueda");
    if (!inputBusqueda) return;
    const query = inputBusqueda.value.toLowerCase();
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

    const cartCountElem = document.getElementById("cart-count");
    const carritoTotalElem = document.getElementById("carrito-total");
    if (cartCountElem) cartCountElem.innerText = count;
    if (carritoTotalElem) carritoTotalElem.innerText = `$${total.toFixed(2)}`;

    const container = document.getElementById("carrito-items");
    if (!container) return;

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
    if (drawer) drawer.classList.toggle("hidden");
}

function obtenerUsuarioLogueado() {
    const userStr = localStorage.getItem('usuario_fajas');
    return userStr ? JSON.parse(userStr) : null;
}

function actualizarBotonCuentaNav() {
    const usuario = obtenerUsuarioLogueado();
    const nombreNav = document.getElementById('nombre-usuario-nav');
    if (!nombreNav) return;
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
    const modal = document.getElementById('modal-auth');
    if (modal) modal.classList.remove('hidden');
}

function cerrarModalAuth() {
    const modal = document.getElementById('modal-auth');
    if (modal) modal.classList.add('hidden');
}

function cambiarTabAuth(tipo) {
    const btnLogin = document.getElementById('tab-login-btn');
    const btnReg = document.getElementById('tab-registro-btn');
    const boxLogin = document.getElementById('form-login-container');
    const boxReg = document.getElementById('form-registro-container');
    if (!btnLogin || !btnReg || !boxLogin || !boxReg) return;

    if (tipo === 'login') {
        btnLogin.className = "flex-1 pb-2 font-bold text-sm text-rose-600 border-b-2 border-rose-600";
        btnReg.className = "flex-1 pb-2 font-bold text-sm text-slate-400";
        boxLogin.classList.remove('hidden');
        boxReg.classList.add('hidden');
    } else {
        btnReg.className = "flex-1 pb-2 font-bold text-sm text-rose-600 border-b-2 border-rose-600";
        btnLogin.className = "flex-1 pb-2 font-bold text-sm text-slate-400";
        boxReg.classList.add('hidden');
        boxLogin.classList.remove('hidden');
    }
}

function toggleVisibilidadPassword(inputId, iconId) {
    const input = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
    if (!input || !icon) return;
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
            alert("Error: " + (data.detail || JSON.stringify(data)));
        }
    } catch (e) {
        alert("Error de conexión con el servidor.");
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
        alert("⚠️ Las contraseñas no coinciden.");
        return;
    }

    try {
        const res = await fetch('/api/web/auth/registro', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, correo, password, telefono, direccion })
        });
        const data = await res.json();

        if (res.ok && data.status === 'success') {
            localStorage.setItem('usuario_fajas', JSON.stringify(data.cliente));
            cerrarModalAuth();
            actualizarBotonCuentaNav();
            alert(data.mensaje);
        } else {
            let errorMsg = data.detail || "Error al registrarse.";
            alert("Error: " + errorMsg);
        }
    } catch (e) {
        alert("Error de conexión con el servidor.");
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
            container.innerHTML = `<div class="text-center py-8 text-slate-400 text-xs">Aún no tienes compras registradas.</div>`;
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
    const modal = document.getElementById('modal-perfil');
    if (modal) modal.classList.add('hidden');
}

function cerrarSesion() {
    localStorage.removeItem('usuario_fajas');
    cerrarModalPerfil();
    actualizarBotonCuentaNav();
    alert("Has cerrado sesión correctamente.");
}

inicializarTienda();