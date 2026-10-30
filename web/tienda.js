const API_URL = "/api/web/inventario";
const API_CATEGORIAS = "/api/web/categorias";
const API_HOME_CONFIG = "/api/web/home-config";
const SVG_FALLBACK = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'><rect width='100%' height='100%' fill='%23f1f5f9'/><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' fill='%2394a3b8' font-size='10'>Fajas Isabella</text></svg>";

let productos = [];
let productosFiltrados = [];
let categoriasOficiales = [];
let productoSeleccionado = null;
let tallaSeleccionada = "";
let colorSeleccionado = "";
let cantidadSeleccionada = 1;
let carrito = [];
let categoriaSeleccionadaActual = "INICIO";
let whatsappUrlGlobal = "https://wa.me/593983870398";

// Variables para Plan Acumulativo
let esPlanAcumulativoActivo = false;

let currentSlide = 0;
let slideInterval = null;

// ==========================================
// 1. INICIALIZACIÓN Y SLIDER
// ==========================================

document.addEventListener("DOMContentLoaded", () => {
    inicializarTienda();
});

async function inicializarTienda() {
    await cargarConfiguracionEmpresa();
    await cargarSeccionInicio();
    await cargarInventario();
    irAInicio();
    actualizarBotonCuentaNav();
}

function iniciarHeroSlider() {
    if (slideInterval) clearInterval(slideInterval);
    slideInterval = setInterval(() => { siguienteSlide(); }, 3000);
}

function siguienteSlide() {
    const slides = document.querySelectorAll('.hero-slide');
    if (!slides.length) return;
    currentSlide = (currentSlide + 1) % slides.length;
    mostrarSlide(currentSlide);
}

function irASlide(index) {
    currentSlide = index;
    mostrarSlide(currentSlide);
    iniciarHeroSlider(); 
}

function mostrarSlide(index) {
    const slides = document.querySelectorAll('.hero-slide');
    const dots = document.querySelectorAll('.hero-dot');
    if (!slides.length) return;
    
    slides.forEach((slide, i) => {
        if (i === index) {
            slide.classList.remove('opacity-0');
            slide.classList.add('opacity-100');
        } else {
            slide.classList.remove('opacity-100');
            slide.classList.add('opacity-0');
        }
    });

    dots.forEach((dot, i) => {
        if (i === index) {
            dot.classList.remove('bg-white/50', 'opacity-60');
            dot.classList.add('bg-white', 'opacity-100');
        } else {
            dot.classList.remove('bg-white', 'opacity-100');
            dot.classList.add('bg-white/50', 'opacity-60');
        }
    });
}

// ==========================================
// 2. CARGA DE CONFIGURACIÓN Y CONTENIDO DINÁMICO
// ==========================================

async function cargarSeccionInicio() {
    const container = document.getElementById('secciones-intro-container');
    if (!container) return;
    try {
        await cargarConfiguracionHomeDinamica();
    } catch (err) {
        console.error("Error al cargar la estructura del home:", err);
    }
}

async function cargarConfiguracionHomeDinamica() {
    const slidesDefault = [
        { tag: "Alta Compresión", titulo: "Moldea tu Figura al Instante", descripcion: "Descubre la nueva línea de fajas reductoras y postoperatorias de máxima comodidad.", btn_texto: "Ver Colección →", imagen: "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=1200&q=80" },
        { tag: "Calidad Colombiana", titulo: "Recuperación y Cuidado Seguro", descripcion: "Diseños especializados con microcápsulas y costuras invisibles para tu diario vivir.", btn_texto: "Explorar Modelos →", imagen: "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=1200&q=80" },
        { tag: "Efecto Cintura", titulo: "Definición Reloj de Arena", descripcion: "Cinturillas de látex térmico ideales para moldear postura y reducir medidas.", btn_texto: "Ver Cinturillas →", imagen: "https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=1200&q=80" },
        { tag: "Envíos Seguros", titulo: "Envíos Directos a Todo Ecuador", descripcion: "Garantía de fábrica directa hasta la puerta de tu hogar.", btn_texto: "Comprar Ahora →", imagen: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=1200&q=80" }
    ];

    let slidesUsar = slidesDefault;
    let dataGlobal = {};

    try {
        const res = await fetch(API_HOME_CONFIG);
        if (res.ok) {
            dataGlobal = await res.json();
            if (dataGlobal.sec05 && typeof dataGlobal.sec05 === 'object') {
                let slidesDinamicos = [];
                for (let i = 1; i <= 4; i++) {
                    const slide = dataGlobal.sec05[`slide${i}`];
                    if (slide && slide.titulo) {
                        let rawImg = slide.imagen || "";
                        let imgUrl = rawImg ? obtenerRutaImagenProducto(rawImg) : slidesDefault[i - 1].imagen;
                        slidesDinamicos.push({
                            tag: slide.tag || "Colección",
                            titulo: slide.titulo,
                            descripcion: slide.descripcion || "",
                            btn_texto: slide.btn_texto || "Ver Colección →",
                            imagen: imgUrl
                        });
                    }
                }
                if (slidesDinamicos.length > 0) slidesUsar = slidesDinamicos;
            }
        }
    } catch (e) {
        console.warn("Usando slider por defecto.");
    }

    let slidesHtml = '';
    let dotsHtml = '';

    slidesUsar.forEach((slide, idx) => {
        let isActive = idx === 0 ? 'opacity-100' : 'opacity-0';
        slidesHtml += `
            <div class="hero-slide absolute inset-0 ${isActive} transition-opacity duration-700 ease-in-out">
                <img src="${slide.imagen}" onerror="this.onerror=null; this.src='${SVG_FALLBACK}'" class="w-full h-full object-cover" alt="${slide.titulo}">
                <div class="absolute inset-0 bg-gradient-to-r from-slate-950/80 via-slate-950/40 to-transparent flex items-center p-6 sm:p-10">
                    <div class="max-w-lg text-white space-y-2">
                        <span class="bg-rose-600 text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase tracking-wider">${slide.tag}</span>
                        <h2 class="text-2xl sm:text-4xl font-extrabold tracking-tight leading-tight">${slide.titulo}</h2>
                        <p class="text-xs sm:text-sm text-slate-200">${slide.descripcion}</p>
                        <button onclick="filtrarCategoria('TODAS')" class="mt-2 inline-block bg-white text-slate-900 hover:bg-rose-600 hover:text-white font-bold text-xs px-4 py-2 rounded-xl transition shadow-md cursor-pointer">${slide.btn_texto}</button>
                    </div>
                </div>
            </div>
        `;
        dotsHtml += `<button onclick="irASlide(${idx})" class="hero-dot w-2.5 h-2.5 rounded-full ${idx === 0 ? 'bg-white opacity-100' : 'bg-white/50 opacity-60'} transition-all cursor-pointer"></button>`;
    });

    const sliderContainer = document.getElementById('hero-slider-container');
    const dotsContainer = document.getElementById('hero-dots-container');
    if (sliderContainer) sliderContainer.innerHTML = slidesHtml;
    if (dotsContainer) dotsContainer.innerHTML = dotsHtml;
    iniciarHeroSlider();

    if (dataGlobal.sec1) {
        const s1 = dataGlobal.sec1;
        if (document.getElementById('sec1-titulo')) document.getElementById('sec1-titulo').innerText = s1.titulo || "HISTORIA";
        if (document.getElementById('sec1-subtitulo')) document.getElementById('sec1-subtitulo').innerText = s1.subtitulo || "";
        if (document.getElementById('sec1-p1')) document.getElementById('sec1-p1').innerText = s1.parrafo1 || "";
        if (document.getElementById('sec1-p2')) document.getElementById('sec1-p2').innerText = s1.parrafo2 || "";
        if (document.getElementById('sec1-p3')) document.getElementById('sec1-p3').innerText = s1.parrafo3 || "";

        const mediaName = s1.multimedia || "banner_historia.jpg";
        const mediaUrl = obtenerRutaImagenProducto(mediaName);
        const imgElem = document.getElementById('home-historia-img');
        const vidElem = document.getElementById('home-historia-video');
        const sourceElem = document.getElementById('home-historia-video-source');

        if (mediaName.endsWith('.mp4')) {
            if (imgElem) imgElem.style.display = 'none';
            if (vidElem && sourceElem) { sourceElem.src = mediaUrl; vidElem.style.display = 'block'; vidElem.load(); }
        } else {
            if (vidElem) vidElem.style.display = 'none';
            if (imgElem) { imgElem.src = mediaUrl; imgElem.style.display = 'block'; }
        }
    }

    if (dataGlobal.sec2) {
        const s2 = dataGlobal.sec2;
        const igContainer = document.getElementById('instagram-embed-container');
        if (igContainer && s2.instagram_embed) {
            igContainer.innerHTML = s2.instagram_embed;
            if (window.instgrm) window.instgrm.Embeds.process();
        }
        const tkBtn = document.getElementById('sec2-tk-btn');
        if (tkBtn && s2.tiktok_url) tkBtn.href = s2.tiktok_url;
    }

    if (dataGlobal.sec3) {
        for (let i = 1; i <= 3; i++) {
            const card = dataGlobal.sec3[`card${i}`];
            if (!card) continue;
            if (document.getElementById(`pub${i}-tag`)) document.getElementById(`pub${i}-tag`).innerText = card.tag || "";
            if (document.getElementById(`pub${i}-titulo`)) document.getElementById(`pub${i}-titulo`).innerText = card.titulo || "";
            if (document.getElementById(`pub${i}-desc`)) document.getElementById(`pub${i}-desc`).innerText = card.descripcion || "";
            if (document.getElementById(`pub${i}-link`)) document.getElementById(`pub${i}-link`).innerText = card.link_texto || "Ver más →";

            const pubMedia = card.multimedia || `publi_${i}.jpg`;
            const pubUrl = obtenerRutaImagenProducto(pubMedia);
            const pubImg = document.getElementById(`pub${i}-img`);
            const pubVid = document.getElementById(`pub${i}-video`);
            const pubSource = document.getElementById(`pub${i}-video-source`);

            if (pubMedia.endsWith('.mp4')) {
                if (pubImg) pubImg.style.display = 'none';
                if (pubVid && pubSource) { pubSource.src = pubUrl; pubVid.style.display = 'block'; pubVid.load(); }
            } else {
                if (pubVid) pubVid.style.display = 'none';
                if (pubImg) { pubImg.src = pubUrl; pubImg.style.display = 'block'; }
            }
        }
    }
}

async function cargarConfiguracionEmpresa() {
    try {
        const res = await fetch("/config/empresa");
        if (res.ok) {
            const data = await res.json();
            if (data.telefono_whatsapp) whatsappUrlGlobal = `https://wa.me/${data.telefono_whatsapp}`;
            if (data.redes) {
                if (document.getElementById("footer-instagram")) document.getElementById("footer-instagram").href = data.redes.instagram;
                if (document.getElementById("footer-facebook")) document.getElementById("footer-facebook").href = data.redes.facebook;
                if (document.getElementById("footer-tiktok")) document.getElementById("footer-tiktok").href = data.redes.tiktok;
                if (document.getElementById("footer-whatsapp")) document.getElementById("footer-whatsapp").href = data.redes.whatsapp;
            }
            if (document.getElementById("footer-direccion")) document.getElementById("footer-direccion").innerText = data.direccion || "";
            if (document.getElementById("footer-telefono")) document.getElementById("footer-telefono").innerText = data.telefono_whatsapp || "";
            if (document.getElementById("footer-correo")) document.getElementById("footer-correo").innerText = data.correo || "";
        }
    } catch (e) { console.warn("Error cargando configuración de empresa."); }
}

async function cargarInventario() {
    try {
        const [resProductos, resCategorias] = await Promise.allSettled([fetch(API_URL), fetch(API_CATEGORIAS)]);
        productos = (resProductos.status === 'fulfilled' && resProductos.value.ok) ? await resProductos.value.json() : [];
        categoriasOficiales = (resCategorias.status === 'fulfilled' && resCategorias.value.ok) ? await resCategorias.value.json() : [];
    } catch (e) {
        productos = [];
        categoriasOficiales = [];
    }
    productosFiltrados = [...productos];
    cargarCategoriasWeb();
    renderizarNovedadesEnHome();
}

function obtenerRutaImagenProducto(imagenUrl) {
    if (!imagenUrl) return SVG_FALLBACK;
    let urlLimpia = String(imagenUrl).trim();
    if (urlLimpia === "" || urlLimpia === "/logo.png" || urlLimpia === "logo.png") return SVG_FALLBACK;
    if (urlLimpia.startsWith("http://") || urlLimpia.startsWith("https://") || urlLimpia.startsWith("/")) return urlLimpia;
    if (urlLimpia.includes('.') && !urlLimpia.startsWith('img/')) {
        return `https://res.cloudinary.com/d82ff3dh/image/upload/v1793225915/fajas_isabella/home/${urlLimpia}`;
    }
    return `/img/${urlLimpia.split('/').pop().trim()}`;
}

// ==========================================
// 3. NAVEGACIÓN Y CATÁLOGO
// ==========================================

function cargarCategoriasWeb() {
    const contenedor = document.getElementById("categorias-scroll");
    const dropdownContainer = document.getElementById("dropdown-categorias-dinamico");
    if (!contenedor) return;
    
    let htmlScroll = `
        <button onclick="filtrarCategoria('TODAS')" id="btn-cat-INICIO" class="btn-categoria flex flex-col items-center shrink-0 focus:outline-none cursor-pointer group w-20">
            <div class="circle-cat w-14 h-14 min-w-[3.5rem] min-h-[3.5rem] rounded-full overflow-hidden border-2 border-slate-200 p-0.5 transition-all shadow-xs bg-rose-50 flex items-center justify-center shrink-0">
                <img src="/img/cat-todas.jpg" onerror="this.onerror=null; this.src='${SVG_FALLBACK}'" class="w-full h-full object-cover rounded-full" alt="Todas">
            </div>
            <span class="text-[9px] font-bold text-slate-700 mt-1 uppercase tracking-tight text-center leading-tight line-clamp-2 w-full">Todas</span>
        </button>
    `;

    let htmlDropdown = `
        <a href="#inicio" onclick="irAInicio()" class="block px-4 py-2 hover:bg-rose-50 text-slate-700 hover:text-rose-600 font-medium">🏠 Inicio / Bienvenida</a>
        <a href="#catalogo" onclick="filtrarCategoria('TODAS')" class="block px-4 py-2 hover:bg-rose-50 text-slate-700 hover:text-rose-600 font-medium">✨ Ver Todo el Catálogo</a>
        <div class="border-t border-slate-100 my-1"></div>
    `;

    if (Array.isArray(categoriasOficiales)) {
        categoriasOficiales.forEach(catObj => {
            const nombreCat = catObj.nombre || catObj.categoria;
            if (!nombreCat) return;
            let imgCat = obtenerRutaImagenProducto(catObj.imagen_url || catObj.imagen || "");

            htmlScroll += `
                <button onclick="filtrarCategoria('${nombreCat}')" id="btn-cat-${nombreCat}" class="btn-categoria flex flex-col items-center shrink-0 focus:outline-none cursor-pointer group w-20">
                    <div class="circle-cat w-14 h-14 min-w-[3.5rem] min-h-[3.5rem] rounded-full overflow-hidden border-2 border-slate-200 p-0.5 transition-all shadow-xs bg-rose-50 flex items-center justify-center shrink-0">
                        <img src="${imgCat}" onerror="this.onerror=null; this.src='${SVG_FALLBACK}'" class="w-full h-full object-cover rounded-full" alt="${nombreCat}">
                    </div>
                    <span class="text-[9px] font-bold text-slate-700 mt-1 uppercase tracking-tight text-center leading-tight line-clamp-2 w-full">${nombreCat}</span>
                </button>
            `;
            htmlDropdown += `<a href="#catalogo" onclick="filtrarCategoria('${nombreCat}')" class="block px-4 py-2 hover:bg-rose-50 text-slate-700 hover:text-rose-600 font-medium">${nombreCat}</a>`;
        });
    }

    contenedor.innerHTML = htmlScroll;
    if (dropdownContainer) dropdownContainer.innerHTML = htmlDropdown;
}

function generarHTMLTarjetaProducto(p) {
    const variantes = p.variantes || [];
    const descuento = Number(p.descuento_oferta || 0);
    let preciosTextoHtml = "";

    if (variantes.length > 0) {
        const preciosCalculados = variantes.map(v => {
            let precioV = Number(v.precio || 0);
            if ((p.en_oferta || p.en_liquidacion) && descuento > 0) precioV = Math.max(0, precioV - descuento);
            return precioV;
        });

        const precioMin = Math.min(...preciosCalculados);
        const precioMax = Math.max(...preciosCalculados);
        const precioMinOrig = Math.min(...variantes.map(v => Number(v.precio || 0)));

        if ((p.en_oferta || p.en_liquidacion) && descuento > 0) {
            preciosTextoHtml = precioMin === precioMax 
                ? `<div class="flex items-center gap-2"><span class="text-xs text-slate-400 line-through">$${precioMinOrig.toFixed(2)}</span><span class="text-sm font-black text-rose-600">$${precioMin.toFixed(2)}</span></div>`
                : `<div class="flex items-center gap-1"><span class="text-[10px] text-slate-400 line-through">$${precioMinOrig.toFixed(2)}</span><span class="text-sm font-black text-rose-600">$${precioMin.toFixed(2)} - $${precioMax.toFixed(2)}</span></div>`;
        } else {
            preciosTextoHtml = precioMin === precioMax 
                ? `<span class="text-sm font-black text-slate-900">$${precioMin.toFixed(2)}</span>`
                : `<span class="text-sm font-black text-slate-900">$${precioMin.toFixed(2)} - $${precioMax.toFixed(2)}</span>`;
        }
    } else {
        preciosTextoHtml = `<span class="text-sm font-black text-slate-900">$0.00</span>`;
    }

    const coloresUnicos = variantes.length > 0 ? [...new Set(variantes.map(v => v.color))].join(", ") : "Variados";
    let badgePromo = '';
    if (p.en_liquidacion) badgePromo = `<span class="absolute top-2 left-2 bg-rose-600 text-white text-[9px] font-black px-2 py-0.5 rounded-full shadow-md animate-pulse">🔥 LIQUIDACIÓN</span>`;
    else if (p.en_oferta) badgePromo = `<span class="absolute top-2 left-2 bg-amber-500 text-white text-[9px] font-black px-2 py-0.5 rounded-full shadow-md">🏷️ OFERTA</span>`;
    else if (p.es_nuevo) badgePromo = `<span class="absolute top-2 left-2 bg-blue-600 text-white text-[9px] font-black px-2 py-0.5 rounded-full shadow-md">✨ NUEVO</span>`;

    const imgSrc = obtenerRutaImagenProducto(p.imagen_url);

    return `
        <div class="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs hover:shadow-lg transition flex flex-col justify-between group">
            <div class="relative bg-slate-50 h-64 w-full flex items-center justify-center p-3 overflow-hidden">
                ${badgePromo}
                <img src="${imgSrc}" onerror="this.onerror=null; this.src='${SVG_FALLBACK}'" class="w-full h-full object-contain group-hover:scale-105 transition-all duration-300" alt="${p.nombre}">
                <span class="absolute top-2 right-2 bg-slate-900/80 text-white text-[9px] font-bold px-2 py-0.5 rounded-full backdrop-blur-xs">${variantes.length} Opciones</span>
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
                    <button onclick="abrirModal(${p.id})" class="bg-slate-900 hover:bg-rose-600 text-white font-bold text-[10px] px-2.5 py-1.5 rounded-xl transition shadow-xs cursor-pointer">Ver Tallas</button>
                </div>
            </div>
        </div>
    `;
}

function renderizarCatalogo() {
    const container = document.getElementById("catalog-container");
    const contadorElem = document.getElementById("total-productos");
    if (!container) return;
    if (contadorElem) contadorElem.innerText = `${productosFiltrados.length} modelos`;

    if (productosFiltrados.length === 0) {
        container.innerHTML = `<div class="col-span-full text-center py-12 text-slate-400 text-sm">No encontramos modelos en esta categoría.</div>`;
    } else {
        container.innerHTML = productosFiltrados.map(p => generarHTMLTarjetaProducto(p)).join('');
    }
}

function irAInicio() {
    categoriaSeleccionadaActual = 'INICIO';
    
    const introContainer = document.getElementById('secciones-intro-container');
    if (introContainer) introContainer.style.display = 'block';

    const catalogoSec = document.getElementById('catalogo');
    if (catalogoSec) catalogoSec.style.display = 'none';

    renderizarNovedadesEnHome();
    iniciarHeroSlider();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderizarNovedadesEnHome() {
    let contenedorDestacados = document.getElementById('home-destacados-home');
    
    if (!contenedorDestacados) {
        const seccionesIntro = document.querySelectorAll('#secciones-intro-container > section');
        const seccionPublicidad = seccionesIntro[seccionesIntro.length - 1];
        
        if (seccionPublicidad) {
            contenedorDestacados = document.createElement('section');
            contenedorDestacados.id = 'home-destacados-home';
            contenedorDestacados.className = 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10';
            seccionPublicidad.parentNode.insertBefore(contenedorDestacados, seccionPublicidad);
        }
    }

    if (!contenedorDestacados) return;

    const destacados = productos.filter(p => p.en_oferta || p.es_nuevo || p.en_liquidacion).slice(0, 5);

    if (destacados.length === 0) {
        contenedorDestacados.innerHTML = '';
        return;
    }

    let htmlCards = destacados.map(p => generarHTMLTarjetaProducto(p)).join('');

    contenedorDestacados.innerHTML = `
        <div class="mb-6 pb-3 border-b border-slate-200 flex items-center justify-between">
            <div>
                <span class="text-rose-600 font-bold text-xs uppercase tracking-wider">Colección Exclusiva</span>
                <h3 class="text-xl font-black text-slate-900">✨ Novedades y Promociones Destacadas</h3>
            </div>
            <button onclick="filtrarCategoria('TODAS')" class="text-xs font-bold text-rose-600 hover:text-rose-700 transition cursor-pointer">Ver todo el catálogo →</button>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            ${htmlCards}
        </div>
    `;
}

function filtrarCategoria(cat) {
    categoriaSeleccionadaActual = cat;
    const tituloCatElem = document.getElementById("titulo-categoria");
    const introContainer = document.getElementById("secciones-intro-container");
    const catalogoSec = document.getElementById("catalogo");

    if (cat === 'INICIO' || cat === 'HOME') {
        irAInicio();
        return;
    }

    if (introContainer) introContainer.style.display = 'none';
    if (catalogoSec) catalogoSec.style.display = 'block';

    if (cat === 'TODAS') {
        if (tituloCatElem) tituloCatElem.innerText = "Todas las Prendas Disponibles";
        productosFiltrados = [...productos];
    } else {
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
    renderizarSeccionesSecundariasCategoria(cat);

    if (catalogoSec) catalogoSec.scrollIntoView({ behavior: 'smooth' });
}

function renderizarSeccionesSecundariasCategoria(catSeleccionada) {
    let contenedor = document.getElementById("secciones-secundarias-container");
    const catalogoSec = document.getElementById("catalogo");

    if (!contenedor && catalogoSec) {
        contenedor = document.createElement("div");
        contenedor.id = "secciones-secundarias-container";
        catalogoSec.appendChild(contenedor);
    }
    if (!contenedor) return;

    let htmlSecundario = '';

    if (catSeleccionada !== 'TODAS') {
        const productosNuevos = productos.filter(p => p.es_nuevo === true);
        const productosOfertas = productos.filter(p => p.en_oferta === true || p.en_liquidacion === true);

        if (catSeleccionada !== 'NEW' && productosNuevos.length > 0) {
            htmlSecundario += `
                <div class="mt-6 pt-4 border-t border-slate-200">
                    <div class="flex items-center justify-between mb-4">
                        <div>
                            <span class="text-blue-600 font-bold text-xs uppercase tracking-wider">✨ Recién Llegados</span>
                            <h3 class="text-lg font-black text-slate-900">Lo Nuevo de Fajas Isabella</h3>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                        ${productosNuevos.map(p => generarHTMLTarjetaProducto(p)).join('')}
                    </div>
                </div>
            `;
        }

        if (catSeleccionada !== 'OFERTAS' && catSeleccionada !== 'LIQUIDACION' && productosOfertas.length > 0) {
            htmlSecundario += `
                <div class="mt-6 pt-4 border-t border-slate-200">
                    <div class="flex items-center justify-between mb-4">
                        <div>
                            <span class="text-amber-600 font-bold text-xs uppercase tracking-wider">🏷️ Descuentos Especiales</span>
                            <h3 class="text-lg font-black text-slate-900">Prendas en Oferta</h3>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                        ${productosOfertas.map(p => generarHTMLTarjetaProducto(p)).join('')}
                    </div>
                </div>
            `;
        }
    }

    const secPublicidadOriginal = document.querySelector('#secciones-intro-container section:last-child');
    if (secPublicidadOriginal) {
        htmlSecundario += `
            <div class="mt-6 pt-4 border-t border-slate-200">
                ${secPublicidadOriginal.outerHTML}
            </div>
        `;
    }

    contenedor.innerHTML = htmlSecundario;
}

function scrollCategorias(distancia) {
    const contenedor = document.getElementById("categorias-scroll");
    if (contenedor) contenedor.scrollBy({ left: distancia, behavior: 'smooth' });
}

function buscarProducto() {
    const inputBusqueda = document.getElementById("input-busqueda");
    if (!inputBusqueda) return;
    const query = inputBusqueda.value.toLowerCase();
    if (query.trim() !== "") filtrarCategoria('TODAS');
    productosFiltrados = productos.filter(p => p.nombre.toLowerCase().includes(query) || p.categoria.toLowerCase().includes(query) || (p.variantes && p.variantes.some(v => v.sku.toLowerCase().includes(query))));
    renderizarCatalogo();
}

// ==========================================
// 4. MODAL DE PRODUCTO Y VARIANTES (ESTILO SALOME)
// ==========================================

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
    const primerPrecio = varianteInicial ? varianteInicial.precio : (variantes[0] ? variantes[0].precio : 0);
    const descuento = Number(productoSeleccionado.descuento_oferta || 0);
    const precioFinalModal = (productoSeleccionado.en_oferta || productoSeleccionado.en_liquidacion) && descuento > 0 ? Math.max(0, primerPrecio - descuento) : primerPrecio;

    // Recopilar elementos multimedia disponibles
    let listaMedia = [];
    if (productoSeleccionado.imagen_url) listaMedia.push({ tipo: 'img', url: productoSeleccionado.imagen_url });
    if (productoSeleccionado.imagen_1) listaMedia.push({ tipo: 'img', url: productoSeleccionado.imagen_1 });
    if (productoSeleccionado.imagen_2) listaMedia.push({ tipo: 'img', url: productoSeleccionado.imagen_2 });
    if (productoSeleccionado.imagen_3) listaMedia.push({ tipo: 'img', url: productoSeleccionado.imagen_3 });
    if (productoSeleccionado.imagen_4) listaMedia.push({ tipo: 'img', url: productoSeleccionado.imagen_4 });
    if (productoSeleccionado.video_url) listaMedia.push({ tipo: 'video', url: productoSeleccionado.video_url });

    // Miniaturas laterales agrandadas (w-20 h-20)
    let thumbsHTML = '';
    listaMedia.forEach((item) => {
        const itemUrl = obtenerRutaImagenProducto(item.url);
        if (item.tipo === 'img') {
            thumbsHTML += `
                <button onclick="cambiarMediaModal('${itemUrl}', false)" class="w-20 h-20 rounded-xl overflow-hidden border-2 border-slate-200 hover:border-rose-600 focus:border-rose-600 transition shrink-0 cursor-pointer shadow-2xs">
                    <img src="${itemUrl}" class="w-full h-full object-cover">
                </button>
            `;
        } else if (item.tipo === 'video') {
            thumbsHTML += `
                <button onclick="cambiarMediaModal('${itemUrl}', true)" class="w-20 h-20 rounded-xl overflow-hidden border-2 border-slate-200 hover:border-rose-600 focus:border-rose-600 transition shrink-0 bg-slate-900 flex items-center justify-center text-white cursor-pointer relative shadow-2xs">
                    <i class="fa-solid fa-play text-sm"></i>
                    <span class="absolute bottom-0 inset-x-0 text-[9px] bg-black/80 text-center font-bold py-0.5">VIDEO</span>
                </button>
            `;
        }
    });

    let cartillaHTML = '';
    if (productoSeleccionado.cartilla_url) {
        const cartillaUrl = obtenerRutaImagenProducto(productoSeleccionado.cartilla_url);
        cartillaHTML = `
            <a href="${cartillaUrl}" target="_blank" class="inline-flex items-center gap-1.5 text-xs font-bold text-rose-600 hover:text-rose-700 bg-rose-50 px-3 py-1.5 rounded-lg border border-rose-200 transition my-1 cursor-pointer">
                <i class="fa-solid fa-ruler-horizontal"></i>
                <span>Guía / Cartilla de Tallas</span>
            </a>
        `;
    }

    const imagenInicialVisor = listaMedia.length > 0 ? obtenerRutaImagenProducto(listaMedia[0].url) : SVG_FALLBACK;

    const contenido = `
        <div class="grid grid-cols-1 md:grid-cols-12 gap-5 items-start">
            
            <!-- COLUMNA IZQUIERDA: MINIATURAS AGRANDADAS (2 cols) -->
            <div class="md:col-span-2 flex md:flex-col gap-2.5 overflow-x-auto md:overflow-y-auto max-h-[480px] no-scrollbar py-1">
                ${thumbsHTML}
            </div>

            <!-- COLUMNA CENTRAL: VISOR PRINCIPAL CUADRADO Y AGRANDADO (5 cols) -->
            <div class="md:col-span-5 relative bg-slate-900 rounded-2xl p-1 border border-slate-100 flex items-center justify-center h-[480px] overflow-hidden shadow-inner" id="modal-visor-principal">
                <img id="modal-imagen-producto" src="${imagenInicialVisor}" onerror="this.onerror=null; this.src='${SVG_FALLBACK}'" class="w-full h-full object-contain rounded-xl transition-all duration-300">
            </div>

            <!-- COLUMNA DERECHA: DETALLES Y COMPRA (5 cols) -->
            <div class="md:col-span-5 space-y-3">
                <div>
                    <span class="text-[10px] font-bold text-rose-600 tracking-wider uppercase">${productoSeleccionado.categoria}</span>
                    <h3 class="text-base font-extrabold text-slate-900 leading-snug mb-1">${productoSeleccionado.nombre}</h3>
                    <p id="modal-precio" class="text-2xl font-black text-rose-600">$${precioFinalModal.toFixed(2)}</p>
                </div>

                ${cartillaHTML}

                <div class="space-y-3 border-t border-slate-100 pt-3">
                    <div>
                        <label class="text-xs font-bold text-slate-800 block mb-1">Talla:</label>
                        <div class="flex gap-2 flex-wrap" id="selector-tallas">
                            ${tallas.map((t, idx) => `<button onclick="seleccionarTalla('${t}')" id="btn-talla-${t}" type="button" class="btn-talla px-3 py-1 text-xs rounded-xl font-bold border ${idx === 0 ? 'bg-rose-600 text-white border-rose-600 shadow-xs' : 'bg-white text-slate-700 border-slate-300'} transition cursor-pointer">${t}</button>`).join('')}
                        </div>
                    </div>
                    <div>
                        <label class="text-xs font-bold text-slate-800 block mb-1">Color:</label>
                        <div class="flex gap-2 flex-wrap" id="selector-colores">
                            ${colores.map((c, idx) => {
                                let bgHex = "#1e293b";
                                const cLower = c.toLowerCase();
                                if (cLower.includes('beige') || cLower.includes('nude') || cLower.includes('arena')) bgHex = "#d4b293";
                                else if (cLower.includes('blanco')) bgHex = "#ffffff";
                                else if (cLower.includes('azul')) bgHex = "#2563eb";
                                else if (cLower.includes('vino') || cLower.includes('rojo')) bgHex = "#9f1239";
                                else if (cLower.includes('gris')) bgHex = "#64748b";
                                return `<button onclick="seleccionarColor('${c}')" id="btn-color-${c}" type="button" class="btn-color flex items-center gap-1.5 px-3 py-1 text-xs rounded-xl font-bold border ${idx === 0 ? 'bg-slate-900 text-white border-slate-900 shadow-xs' : 'bg-white text-slate-700 border-slate-300'} transition cursor-pointer"><span class="w-3 h-3 rounded-full border border-slate-300 inline-block shadow-2xs" style="background-color: ${bgHex};"></span><span>${c}</span></button>`;
                            }).join('')}
                        </div>
                    </div>
                    <div class="bg-rose-50/60 border border-rose-100 p-3 rounded-xl">
                        <div class="text-xs text-slate-800 space-y-1.5">
                            <div class="flex justify-between"><span class="text-slate-500">Variante:</span><span class="font-bold text-slate-900"><span id="resumen-talla">${tallaSeleccionada}</span> / <span id="resumen-color">${colorSeleccionado}</span></span></div>
                            <div class="flex justify-between"><span class="text-slate-500">Disponibilidad:</span><span class="font-mono text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded" id="modal-stock">Consultando...</span></div>
                            <div class="flex justify-between items-center pt-1"><span class="text-slate-700 font-bold">Cantidad:</span><div class="flex items-center border border-slate-300 rounded-lg bg-white overflow-hidden shadow-2xs"><button onclick="cambiarCantidadModal(-1)" type="button" class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-extrabold transition cursor-pointer">-</button><input id="modal-cantidad-input" type="number" value="1" min="1" class="w-8 text-center text-xs font-black border-none outline-none bg-transparent" readonly><button onclick="cambiarCantidadModal(1)" type="button" class="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-extrabold transition cursor-pointer">+</button></div></div>
                            <div class="flex justify-between items-center pt-1 text-sm font-black text-slate-900 border-t border-rose-200/60 mt-1"><span>Total:</span><span id="modal-total-seleccion" class="text-rose-600 text-lg">$0.00</span></div>
                        </div>
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-2 pt-2">
                    <button onclick="agregarAlCarrito(false)" type="button" class="bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-xs py-3 rounded-xl flex items-center justify-center gap-1.5 transition cursor-pointer"><span>Seguir Comprando</span></button>
                    <button onclick="agregarAlCarrito(true)" type="button" class="bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs py-3 rounded-xl flex items-center justify-center gap-1.5 shadow-md shadow-rose-600/20 transition cursor-pointer"><span>Ir al Carrito</span></button>
                </div>
            </div>
        </div>
    `;

    document.getElementById("modal-contenido").innerHTML = contenido;
    document.getElementById("modal-producto").classList.remove("hidden");
    actualizarDetalleVariante();
}

function cambiarMediaModal(url, esVideo) {
    const visor = document.getElementById('modal-visor-principal');
    if (!visor) return;

    if (esVideo) {
        visor.innerHTML = `
            <video controls autoplay class="w-full h-full object-contain rounded-xl bg-black">
                <source src="${url}" type="video/mp4">
            </video>
        `;
    } else {
        visor.innerHTML = `
            <img id="modal-imagen-producto" src="${url}" class="w-full h-full object-contain rounded-xl">
        `;
    }
}

function cambiarCantidadModal(delta) {
    const variante = obtenerVarianteActual();
    const stockMax = variante ? variante.stock : 99;
    cantidadSeleccionada += delta;
    if (cantidadSeleccionada < 1) cantidadSeleccionada = 1;
    if (cantidadSeleccionada > stockMax && stockMax > 0) cantidadSeleccionada = stockMax;
    const inputElem = document.getElementById("modal-cantidad-input");
    if (inputElem) inputElem.value = cantidadSeleccionada;
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
        const urlFoto = (variante && variante.imagen_url && variante.imagen_url.trim() !== "") ? variante.imagen_url : productoSeleccionado.imagen_url;
        imgElem.src = obtenerRutaImagenProducto(urlFoto);
    }
    actualizarDetalleVariante();
}

function actualizarDetalleVariante() {
    const variante = obtenerVarianteActual();
    if (variante && productoSeleccionado) {
        let precioUnitario = variante.precio;
        const descuento = Number(productoSeleccionado.descuento_oferta || 0);
        if ((productoSeleccionado.en_oferta || productoSeleccionado.en_liquidacion) && descuento > 0) precioUnitario = Math.max(0, precioUnitario - descuento);
        const totalLinea = precioUnitario * cantidadSeleccionada;
        document.getElementById("modal-precio").innerText = `$${precioUnitario.toFixed(2)}`;
        document.getElementById("resumen-talla").innerText = tallaSeleccionada;
        document.getElementById("resumen-color").innerText = colorSeleccionado;
        document.getElementById("modal-stock").innerText = `Stock: ${variante.stock} disp.`;
        document.getElementById("modal-total-seleccion").innerText = `$${totalLinea.toFixed(2)}`;
    }
}

function cerrarModal() {
    const modal = document.getElementById("modal-producto");
    if (modal) modal.classList.add("hidden");
}

// ==========================================
// 5. CARRITO Y PLAN ACUMULATIVO
// ==========================================

function agregarAlCarrito(abrirDrawer = false) {
    const variante = obtenerVarianteActual();
    const cantAgregar = cantidadSeleccionada > 0 ? cantidadSeleccionada : 1;
    let precioFinalUnitario = variante.precio;
    const descuento = Number(productoSeleccionado.descuento_oferta || 0);
    if ((productoSeleccionado.en_oferta || productoSeleccionado.en_liquidacion) && descuento > 0) precioFinalUnitario = Math.max(0, precioFinalUnitario - descuento);

    const itemExistente = carrito.find(item => item.sku === variante.sku);
    if (itemExistente) {
        itemExistente.cantidad += cantAgregar;
    } else {
        carrito.push({
            nombre: productoSeleccionado.nombre, sku: variante.sku, talla: tallaSeleccionada, color: colorSeleccionado,
            precio: precioFinalUnitario, imagen_url: productoSeleccionado.imagen_url || SVG_FALLBACK, categoria: productoSeleccionado.categoria, cantidad: cantAgregar
        });
    }
    cerrarModal();
    actualizarCarritoUI();
    if (abrirDrawer) toggleCarrito();
}

function calcularTotalCarrito() {
    if (!carrito || carrito.length === 0) return 0;
    return carrito.reduce((sum, item) => sum + (item.precio * item.cantidad), 0);
}

function togglePlanAcumulativo(activar) {
    esPlanAcumulativoActivo = activar;
    const contenedor = document.getElementById('contenedor-plan-acumulativo');
    
    if (activar && contenedor) {
        contenedor.classList.remove('hidden');
        const totalCarrito = calcularTotalCarrito();
        const abonoSugerido = (totalCarrito * 0.5).toFixed(2);
        const inputAbono = document.getElementById('input-abono-inicial');
        if (inputAbono) inputAbono.value = abonoSugerido;
        calcularSaldoPendiente();
    } else if (contenedor) {
        contenedor.classList.add('hidden');
    }
}

function calcularSaldoPendiente() {
    const totalCarrito = calcularTotalCarrito();
    const abonoInput = parseFloat(document.getElementById('input-abono-inicial')?.value) || 0;
    
    let saldo = totalCarrito - abonoInput;
    if (saldo < 0) saldo = 0;
    
    const textoSaldo = document.getElementById('texto-saldo-pendiente');
    if (textoSaldo) {
        textoSaldo.innerText = `$${saldo.toFixed(2)}`;
    }
}

function generarMensajeWhatsAppFinal() {
    const total = calcularTotalCarrito();
    const nombreCliente = document.getElementById('nombre-cliente')?.value || 'Cliente';
    const telefonoCliente = document.getElementById('telefono-cliente')?.value || '';
    const ciudadCliente = document.getElementById('ciudad-cliente')?.value || '';
    const direccionCliente = document.getElementById('direccion-cliente')?.value || '';

    let mensaje = "";

    if (esPlanAcumulativoActivo) {
        const abonoInicial = parseFloat(document.getElementById('input-abono-inicial')?.value) || 0;
        const saldoPendiente = total - abonoInicial;

        mensaje = `*✨ NUEVA SOLICITUD DE PLAN ACUMULATIVO - FAJAS ISABELLA ✨*\n\n`;
        mensaje += `👤 *Cliente:* ${nombreCliente}\n`;
        mensaje += `📞 *Teléfono:* ${telefonoCliente}\n`;
        mensaje += `📍 *Ciudad/Dirección:* ${ciudadCliente} - ${direccionCliente}\n\n`;
        mensaje += `🛍️ *Detalle de Prendas:* \n`;
        
        carrito.forEach(item => {
            mensaje += `- ${item.cantidad}x ${item.nombre} (Talla: ${item.talla}, Color: ${item.color}) - $${(item.precio * item.cantidad).toFixed(2)}\n`;
        });

        mensaje += `\n💰 *Total del Pedido:* $${total.toFixed(2)}`;
        mensaje += `\n💵 *Abono Inicial Realizado:* $${abonoInicial.toFixed(2)}`;
        mensaje += `\n⏳ *Saldo Pendiente:* $${saldoPendiente.toFixed(2)}`;
        mensaje += `\n\n*Adjunto el comprobante de mi abono inicial para congelar y apartar las prendas.* ¡Quedo atenta/o!`;

    } else {
        mensaje = `*🛍️ NUEVO PEDIDO - FAJAS ISABELLA*\n\n`;
        mensaje += `👤 *Cliente:* ${nombreCliente}\n`;
        mensaje += `📞 *Teléfono:* ${telefonoCliente}\n`;
        mensaje += `📍 *Ciudad/Dirección:* ${ciudadCliente} - ${direccionCliente}\n\n`;
        mensaje += `🛍️ *Productos:* \n`;
        
        carrito.forEach(item => {
            mensaje += `- ${item.cantidad}x ${item.nombre} (Talla: ${item.talla}, Color: ${item.color}) - $${(item.precio * item.cantidad).toFixed(2)}\n`;
        });

        mensaje += `\n💰 *TOTAL A PAGAR:* $${total.toFixed(2)}`;
        mensaje += `\n\n*Adjunto comprobante de pago.* ¡Muchas gracias!`;
    }

    return encodeURIComponent(mensaje);
}

function procesarPedidoWhatsApp() {
    if (carrito.length === 0) {
        alert("Tu carrito está vacío.");
        return;
    }
    const mensaje = generarMensajeWhatsAppFinal();
    const url = `${whatsappUrlGlobal}?text=${mensaje}`;
    window.open(url, '_blank');
}

function actualizarCarritoUI() {
    const count = carrito.reduce((acc, item) => acc + item.cantidad, 0);
    const total = calcularTotalCarrito();
    if (document.getElementById("cart-count")) document.getElementById("cart-count").innerText = count;
    if (document.getElementById("carrito-total")) document.getElementById("carrito-total").innerText = `$${total.toFixed(2)}`;

    if (esPlanAcumulativoActivo) calcularSaldoPendiente();

    const container = document.getElementById("carrito-items");
    if (!container) return;
    if (carrito.length === 0) {
        container.innerHTML = `<div class="text-center py-12 text-slate-400 text-xs">Tu carrito está vacío.</div>`;
        return;
    }

    container.innerHTML = carrito.map((item, index) => `
        <div class="flex items-center justify-between p-3 bg-slate-50 border border-slate-100 rounded-xl">
            <div class="flex items-center gap-3">
                <img src="${obtenerRutaImagenProducto(item.imagen_url)}" onerror="this.onerror=null; this.src='${SVG_FALLBACK}'" class="w-12 h-12 object-contain rounded-lg bg-white p-1 border">
                <div>
                    <h4 class="text-xs font-bold text-slate-800 line-clamp-1">${item.nombre}</h4>
                    <p class="text-[10px] text-slate-500">Talla: <b>${item.talla}</b> | Color: <b>${item.color}</b></p>
                    <span class="text-xs font-black text-rose-600">$${item.precio.toFixed(2)} x ${item.cantidad}</span>
                </div>
            </div>
            <button onclick="eliminarDelCarrito(${index})" class="text-slate-400 hover:text-rose-600 text-xs p-1 cursor-pointer"><i class="fa-solid fa-trash-can"></i></button>
        </div>
    `).join('');
}

function eliminarDelCarrito(index) {
    carrito.splice(index, 1);
    actualizarCarritoUI();
}

function toggleCarrito() {
    const drawer = document.getElementById("drawer-carrito");
    if (!drawer) return;
    
    if (drawer.classList.contains('hidden')) {
        drawer.classList.remove('hidden');
        actualizarCarritoUI();
    } else {
        drawer.classList.add('hidden');
    }
}

// ==========================================
// 6. AUTENTICACIÓN Y PERFIL DE USUARIO
// ==========================================

function obtenerUsuarioLogueado() {
    const userStr = localStorage.getItem('usuario_fajas');
    return userStr ? JSON.parse(userStr) : null;
}

function actualizarBotonCuentaNav() {
    const usuario = obtenerUsuarioLogueado();
    const nombreNav = document.getElementById('nombre-usuario-nav');
    if (!nombreNav) return;
    nombreNav.innerText = usuario ? usuario.nombre.split(' ')[0] : "Mi Cuenta";
}

function gestionarClicCuenta() {
    if (obtenerUsuarioLogueado()) abrirModalPerfil();
    else abrirModalAuth();
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
        btnLogin.className = "flex-1 pb-2 font-bold text-sm text-rose-600 border-b-2 border-rose-600 cursor-pointer";
        btnReg.className = "flex-1 pb-2 font-bold text-sm text-slate-400 cursor-pointer";
        boxLogin.classList.remove('hidden');
        boxReg.classList.add('hidden');
    } else {
        btnReg.className = "flex-1 pb-2 font-bold text-sm text-rose-600 border-b-2 border-rose-600 cursor-pointer";
        btnLogin.className = "flex-1 pb-2 font-bold text-sm text-slate-400 cursor-pointer";
        boxReg.classList.remove('hidden');
        boxLogin.classList.add('hidden');
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
            alert("Error: " + (data.detail || "Credenciales incorrectas"));
        }
    } catch (e) { alert("Error de conexión."); }
}

async function ejecutarRegistro(event) {
    event.preventDefault();
    const nombre = document.getElementById('reg-nombre').value;
    const correo = document.getElementById('reg-correo').value;
    const password = document.getElementById('reg-password').value;
    const passwordConfirm = document.getElementById('reg-password-confirm').value;
    const telefono = document.getElementById('reg-telefono').value;
    const direccion = document.getElementById('reg-direccion').value;

    if (password !== passwordConfirm) { alert("⚠️ Las contraseñas no coinciden."); return; }

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
            alert("Error: " + (data.detail || "No se pudo completar el registro."));
        }
    } catch (e) { alert("Error de conexión."); }
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
                <div class="flex justify-between font-bold text-slate-900"><span>Factura #${p.numero_factura}</span><span class="text-rose-600">$${p.total.toFixed(2)}</span></div>
                <div class="flex justify-between text-slate-500 text-[11px]"><span>Fecha: ${p.fecha}</span><span class="font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">${p.estado_despacho}</span></div>
                <div class="pt-1 border-t border-slate-200 text-[11px] flex justify-between"><span>Courier: <b>${p.courier}</b></span><span>Guía: <b>${p.numero_guia}</b></span></div>
            </div>
        `).join('');
    } catch (e) { container.innerHTML = `<div class="text-center py-8 text-rose-500 text-xs">Error al cargar historial.</div>`; }
}

function cerrarModalPerfil() {
    const modal = document.getElementById('modal-perfil');
    if (modal) modal.classList.add('hidden');
}

function cerrarSesion() {
    localStorage.removeItem('usuario_fajas');
    cerrarModalPerfil();
    actualizarBotonCuentaNav();
    alert("Has cerrado sesión.");
}