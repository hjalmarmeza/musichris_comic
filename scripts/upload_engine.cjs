const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

async function uploadVideo() {
    const videoPath = process.argv[2] || 'output_final.mp4';
    const title = (process.env.VIDEO_TITLE || 'Mensaje de Fe') + ' | @MusiChris Studio #Shorts';
    
    let description = (process.env.VIDEO_DESCRIPTION || '🌬️ Una palabra de victoria para tu vida hoy.') + '\n\nSuscríbete para más contenido ministerial: @MusiChris Studio\n\n#Shorts #Fe #Cristiano #Victoria';
    if (process.env.VIDEO_DESCRIPTION_FILE && fs.existsSync(process.env.VIDEO_DESCRIPTION_FILE)) {
        description = fs.readFileSync(process.env.VIDEO_DESCRIPTION_FILE, 'utf8');
    }

    console.log('🚀 Iniciando Motor de Subida de MusiChris Studio...');

    if (!process.env.YOUTUBE_CREDENTIALS || !process.env.YOUTUBE_TOKEN) {
        console.error('❌ Error: Faltan secretos YOUTUBE_CREDENTIALS o YOUTUBE_TOKEN.');
        process.exit(1);
    }

    try {
        const credentials = JSON.parse(process.env.YOUTUBE_CREDENTIALS);
        let token;
        try {
            token = JSON.parse(process.env.YOUTUBE_TOKEN);
        } catch (e) {
            // Si no es JSON, asumimos que es el Refresh Token crudo
            token = {
                refresh_token: process.env.YOUTUBE_TOKEN,
                type: 'authorized_user'
            };
        }

        const { client_secret, client_id, redirect_uris } = credentials.installed || credentials.web;
        const auth = new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);
        auth.setCredentials(token);

        const youtube = google.youtube({ version: 'v3', auth });

        console.log(`📤 Subiendo: ${videoPath}`);
        const fileSize = fs.statSync(videoPath).size;

        const tags = process.env.VIDEO_TAGS ? process.env.VIDEO_TAGS.split(',').map(t => t.trim()) : ['MusiChris', 'Aliento', 'Fe'];

        const res = await youtube.videos.insert({
            part: 'snippet,status',
            requestBody: {
                snippet: {
                    title: title.length > 100 ? title.substring(0, 97) + '...' : title,
                    description: description,
                    tags: tags,
                    categoryId: '10' // Music
                },
                status: {
                    privacyStatus: 'unlisted', // Oculto para revisión ministerial
                    selfDeclaredMadeForKids: false
                }
            },
            media: {
                body: fs.createReadStream(videoPath)
            }
        }, {
            onUploadProgress: evt => {
                const progress = (evt.bytesRead / fileSize) * 100;
                process.stdout.write(`\r📊 Progreso de subida: ${Math.round(progress)}%`);
            }
        });

        console.log(`\n✅ ¡GLORIA A DIOS! Video subido con éxito.`);
        console.log(`🔗 ID del Video: ${res.data.id}`);
        console.log(`🔗 URL: https://youtu.be/${res.data.id}`);

        // Subir miniatura si se proporciona
        const thumbnailPath = process.argv[3];
        if (thumbnailPath && fs.existsSync(thumbnailPath)) {
            console.log(`🖼️ Subiendo miniatura: ${thumbnailPath}`);
            await youtube.thumbnails.set({
                videoId: res.data.id,
                media: {
                    body: fs.createReadStream(thumbnailPath)
                }
            });
            console.log('✅ Miniatura establecida correctamente.');
        }

    } catch (error) {
        console.error('❌ Error crítico:', error.message);
        if (error.response) console.error('Detalles:', JSON.stringify(error.response.data));
        process.exit(1);
    }
}

uploadVideo();
