import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import * as Styled from "./styles";
import { getJobStatus } from '../../services/root';
import { toast } from "react-toastify";
import { Header } from '../../components/header';
import { Footer } from '../../components/footer';


interface JobStatusResponse {
    status: 'queued' | 'processing' | 'error' | 'done' | string;
    image_url?: string;
    error?: string;
}


export const Result = () => {
    const [status, setStatus] = useState('Enviando job e aguardando resultado...');
    const [imageUrl, setImageUrl] = useState<string | null>(null);
    const [isZoomVisible, setIsZoomVisible] = useState(false);
    const [bgBackground, setBgBackground] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        const jobId = localStorage.getItem('job_id');
        setBgBackground(localStorage.getItem('bgBackground') || '');
        if (!jobId) {
            setStatus('Nenhum ID de job encontrado.');
            return;
        }

        const checkResult = async () => {
            try {
                const data: JobStatusResponse = await getJobStatus(jobId);
                console.log('Response:', data);

                switch (data.status) {
                    case 'queued':
                        setStatus('Na fila. Aguardando início do processamento...');
                        break;
                    case 'processing':
                        setStatus('Processando imagem...');
                        break;
                    case 'error':
                        setStatus(`Erro: ${data.error || 'Erro desconhecido.'}`);
                        return;
                    case 'done':
                        setStatus('Imagem pronta!');
                        if (data.image_url) setImageUrl(data.image_url);
                        return;
                    default:
                        setStatus('Status desconhecido.');
                        return;
                }
            } catch (err) {
                console.error(err);
                setStatus('Erro ao consultar status do job.');
            }

            setTimeout(checkResult, 2000);
        };

        checkResult();
    }, []);

    const downloadImage = async () => {
        if (!imageUrl) {
            toast.error("Imagem não encontrada. Não conseguimos carregar sua imagem. Tente novamente.");
            return;
        }

        try {
            const response = await fetch(imageUrl, {
                mode: 'cors',
                headers: {
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                },
            });

            const blob = await response.blob();
            const blobUrl = URL.createObjectURL(blob);
            const link = document.createElement('a');
            const randomInt = Math.floor(Math.random() * 90000) + 10000;

            link.href = blobUrl;
            link.download = `${randomInt}_db_IA.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(blobUrl);
        } catch (error) {
            console.error("Erro ao baixar imagem:", error);
            toast.error("Falha no download. Não foi possível baixar a imagem. Tente novamente mais tarde.");
        }
    };

    const shareImage = async () => {
        if (!imageUrl) {
            toast.error("Imagem não disponível para compartilhamento.");
            return;
        }

        try {
            const response = await fetch(imageUrl, {
                headers: {
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                },
            });

            const blob = await response.blob();
            const file = new File([blob], 'db_IA.png', { type: 'image/png' });

            if (navigator.canShare && navigator.canShare({ files: [file] })) {
                await navigator.share({
                    files: [file],
                    title: 'Minha foto Gerada',
                    text: 'Confira minha foto do Gerada!',
                });
            } else {
                toast.error("Compartilhamento de arquivos não suportado neste navegador.");
            }
        } catch (error) {
            console.error("Erro ao compartilhar:", error);
            toast.error("Ocorreu um erro ao tentar compartilhar a imagem.");
        }
    };

    return (
        <Styled.Container backgroundColor={bgBackground}>
            <Header />

            <Styled.Content>

                {!imageUrl && (status.includes('Processando') || status.includes('Na fila') || status.includes('Enviando')) ? (
                    <Styled.CenteredWrapper>
                        <Styled.LoadingCard>
                            <Styled.Status>{status}</Styled.Status>
                            <Styled.SpinnerWrapper />
                        </Styled.LoadingCard>
                    </Styled.CenteredWrapper>
                ) : (
                    <>
                        <h1>Imagem Pronta!</h1>

                        {imageUrl && (
                            <>
                                <Styled.Result>
                                    <img src={imageUrl} alt="Resultado gerado" onClick={() => setIsZoomVisible(true)} />
                                </Styled.Result>

                                {isZoomVisible && (
                                    <Styled.ImageOverlay onClick={() => setIsZoomVisible(false)}>
                                        <img src={imageUrl} alt="Zoom" onClick={(e) => e.stopPropagation()} />
                                    </Styled.ImageOverlay>
                                )}
                            </>
                        )}

                        <Styled.ButtonsContainer>
                            <Styled.BackButton onClick={downloadImage}>
                                Baixar
                            </Styled.BackButton>

                            <Styled.BackButton onClick={shareImage}>
                                Compartilhar
                            </Styled.BackButton>

                            <Styled.BackButton onClick={() => navigate('/')}>
                                Fazer Novamente
                            </Styled.BackButton>
                        </Styled.ButtonsContainer>
                    </>
                )}
            </Styled.Content>
            <Footer />

        </Styled.Container>
    );
};
