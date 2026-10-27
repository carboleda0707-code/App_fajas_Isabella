// home.js - Conexión dinámica con PostgreSQL y Chivato de Estado
if (typeof window.globalInstagramEmbed === 'undefined') {
    window.globalInstagramEmbed = "";
}

window.inicializarHome = async function() {
    const chivato = document.getElementById('chivato-debug');
    
    try {
        if (chivato) chivato.innerHTML = '<span class="text-amber-400 font-bold">⚡ Estado Web:</span> Consultando Base de Datos...';

        // Petición al endpoint de FastAPI que lee PostgreSQL
        const response = await fetch('/api/web/home');
        if (!response.ok) throw new Error("Error al conectar con la API de la tienda");
        
        const data = await response.json();
        
        if (chivato) chivato.innerHTML = '<span class="text-emerald-400 font-bold">✅ Estado Web:</span> Sincronizado con PostgreSQL';

        // SECCIÓN 1: HISTORIA (Textos y Video / Imagen dinámica)
        if (data.sec1) {
            if (document.getElementById('sec1-titulo')) document.getElementById('sec1-titulo').innerText = data.sec1.titulo || "";
            if (document.getElementById('sec1-subtitulo')) document.getElementById('sec1-subtitulo').innerText = data.sec1.subtitulo || "";
            if (document.getElementById('sec1-p1')) document.getElementById('sec1-p1').innerText = data.sec1.parrafo1 || "";
            if (document.getElementById('sec1-p2')) document.getElementById('sec1-p2').innerText = data.sec1.parrafo2 || "";
            if (document.getElementById('sec1-p3')) document.getElementById('sec1-p3').innerText = data.sec1.parrafo3 || "";

            const videoElem = document.getElementById('home-historia-video');
            const videoSourceElem = document.getElementById('home-historia-video-source');
            const imgElem = document.getElementById('home-historia-img');
            
            const rutaMultimedia = data.sec1.multimedia || data.sec1.video || "";

            if (videoElem && videoSourceElem && imgElem) {
                if (rutaMultimedia && rutaMultimedia.toLowerCase().includes('.mp4')) {
                    const nombreArchivo = rutaMultimedia.split('/').pop();
                    videoSourceElem.src = `img/${nombreArchivo}`;
                    videoElem.style.display = 'block';
                    videoElem.load();
                    imgElem.style.display = 'none';
                } else {
                    const nombreImg = rutaMultimedia ? rutaMultimedia.split('/').pop() : 'banner_historia.jpg';
                    imgElem.src = `img/${nombreImg}`;
                    videoElem.style.display = 'none';
                    imgElem.style.display = 'block';
                }
            }
        }

        // SECCIÓN 2: REDES (TikTok URL)
        if (data.sec2) {
            if (data.sec2.tiktok_url && document.getElementById('sec2-tk-btn')) {
                document.getElementById('sec2-tk-btn').href = data.sec2.tiktok_url;
            }
        }

        // SECCIÓN 3: PUBLICIDAD (Soporte dinámico para imágenes o videos desde la BD)
        const renderPub = (num, cardData) => {
            if (!cardData) return;
            
            if (document.getElementById(`pub${num}-tag`)) document.getElementById(`pub${num}-tag`).innerText = cardData.tag || "";
            if (document.getElementById(`pub${num}-titulo`)) document.getElementById(`pub${num}-titulo`).innerText = cardData.titulo || "";
            if (document.getElementById(`pub${num}-desc`)) document.getElementById(`pub${num}-desc`).innerText = cardData.descripcion || "";
            if (document.getElementById(`pub${num}-link`)) document.getElementById(`pub${num}-link`).innerText = cardData.link_texto || "Ver más →";

            const videoElem = document.getElementById(`pub${num}-video`);
            const sourceElem = document.getElementById(`pub${num}-video-source`);
            const imgElem = document.getElementById(`pub${num}-img`);

            const archivo = cardData.multimedia || `publi_${num}.jpg`;

            if (videoElem && sourceElem && imgElem) {
                const nombreArchivo = archivo.split('/').pop();
                if (archivo.toLowerCase().includes('.mp4')) {
                    sourceElem.src = `img/${nombreArchivo}`;
                    videoElem.style.display = 'block';
                    videoElem.load();
                    imgElem.style.display = 'none';
                } else {
                    imgElem.src = `img/${nombreArchivo}`;
                    videoElem.style.display = 'none';
                    imgElem.style.display = 'block';
                }
            }
        };

        if (data.sec3) {
            renderPub(1, data.sec3.card1);
            renderPub(2, data.sec3.card2);
            renderPub(3, data.sec3.card3);
        }

    } catch (e) {
        console.error("Error al cargar la configuración desde la BD:", e);
        if (chivato) {
            chivato.innerHTML = `<span class="text-rose-400 font-bold">❌ Error BD:</span> ${e.message}`;
        }
    }
};

// Autoejecución
document.addEventListener("DOMContentLoaded", () => {
    setTimeout(() => {
        if (typeof window.inicializarHome === 'function') {
            window.inicializarHome();
        }
    }, 300);
});