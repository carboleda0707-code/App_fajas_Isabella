// home.js - Lógica dinámica unificada y limpia
if (typeof window.globalInstagramEmbed === 'undefined') {
    window.globalInstagramEmbed = "";
}

// Configuración unificada directamente en el JS
const homeConfig = {
    "sec1": {
        "titulo": "HISTORIA",
        "subtitulo": "12 AÑOS RESALTANDO TU BELLEZA",
        "parrafo1": "Fajas Isabella empezó vendiendo desde la sala de su casa, con la convicción de que toda mujer merece sentirse segura y hermosa en su cuerpo.",
        "parrafo2": "Hoy somos un equipo que fabrica directamente fajas colombianas, con ventas al por mayor y al por menor, y más de 80 modelos entre fajas látex reductoras, fajas postoperatorias, cinturillas y accesorios.",
        "parrafo3": "Nuestra marca está registrada ante el SENADI como \"FAJAS Isabella RESALTA TU BELLEZA\", un respaldo de la calidad y la confianza que nos han dado nuestras clientas.",
        "multimedia": "banner_historia.mp4"
    },
    "sec2": {
        "tiktok_url": "https://tiktok.com"
    },
    "sec3": {
        "card1": {
            "tag": "PUBLICIDAD 1",
            "titulo": "Moldeadoras de Alta Compresión",
            "descripcion": "Control total y definición perfecta para uso diario.",
            "link_texto": "Ver Colección →",
            "multimedia": "publi_1.jpg",
            "tipo": "img"
        },
        "card2": {
            "tag": "PUBLICIDAD 2",
            "titulo": "Confort y Recuperación Segura",
            "descripcion": "Diseñadas por expertos para garantizar tu bienestar.",
            "link_texto": "Ver Modelos →",
            "multimedia": "publi_2.jpg",
            "tipo": "img"
        },
        "card3": {
            "tag": "PUBLICIDAD 3",
            "titulo": "Reduce Medidas al Instante",
            "descripcion": "Moldea tu cintura con máxima comodidad.",
            "link_texto": "Descubrir →",
            "multimedia": "publi_3.jpg",
            "tipo": "img"
        }
    }
};

window.inicializarHome = async function() {
    try {
        const data = homeConfig;
        
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
            
            const rutaVideo = data.sec1.multimedia || data.sec1.video || "";

            if (videoElem && videoSourceElem && imgElem) {
                if (rutaVideo && rutaVideo.toLowerCase().includes('.mp4')) {
                    const nombreArchivo = rutaVideo.split('/').pop();
                    videoSourceElem.src = `img/${nombreArchivo}`;
                    videoElem.style.display = 'block';
                    videoElem.load();
                    imgElem.style.display = 'none';
                } else {
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

        // SECCIÓN 3: PUBLICIDAD (Soporte dinámico para imágenes o videos)
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
                if (archivo.toLowerCase().includes('.mp4')) {
                    sourceElem.src = `img/${archivo.split('/').pop()}`;
                    videoElem.style.display = 'block';
                    videoElem.load();
                    imgElem.style.display = 'none';
                } else {
                    imgElem.src = `img/${archivo.split('/').pop()}`;
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
        console.error("Error al cargar la configuración:", e);
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