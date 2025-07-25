import { Footer } from "../../components/footer";
import { Header } from "../../components/header";
import * as Styled from "./styles";
import PlusButton from "../../assets/imgs/bt_mais.png"
import { useEffect, useRef, useState } from "react";
import { uploadImage } from "../../services/root";
import { toast } from "react-toastify";
import BTGerar from "../../assets/imgs/bt_gerar.png"
import BTGerarDesk from "../../assets/imgs/bt_gerar_desk.png"
import OrfeuBackground from "../../assets/imgs/orfeu.png";
import AmtelBackground from "../../assets/imgs/amstel.png";
import CaixaBackground from "../../assets/imgs/caixa1.png";
import ArrowLeft from "../../assets/imgs/BT_carrossel_es_seta.png";
import ArrowRight from "../../assets/imgs/BT_carrossel_dir_seta.png";
import type { IProject } from "../../types";
import { useMediaQuery } from "../../hooks/useMediaQuery";
import { useNavigate } from "react-router";


export const Home = () => {
    const projects: IProject[] = [
        {
            imageBackground: OrfeuBackground,
            inputContainerColor: '#2B5234',
            tittleText: 'ORFEU ART',
            text: 'A experiência transforma fotos em obras de arte inspiradas no modernismo brasileiro, com traços geométricos, cores marcantes e textura de pintura. Um convite visual à sofisticação e à brasilidade da marca.',
            projectName: 'orfeu_production_model_v11.json'
        },
        {
            imageBackground: AmtelBackground,
            inputContainerColor: '#901111',
            tittleText: 'AMSTEL KINGSDAY',
            text: "Utiliza inteligência artificial para transformar fotos em retratos estilizados de reis e rainhas, com coroas, tecidos nobres e ambientação dourada. A estética celebra o visual festivo do King's Day, criando uma lembrança visual alinhada ao conceito da campanha.",
            projectName: 'amstel_production_model_v14.json'
        },
        {
            imageBackground: CaixaBackground,
            inputContainerColor: '#0C91DD',
            tittleText: 'CAIXA MAMULENGO',
            text: 'Transforma a imagem do público em um boneco de papel machê com estética inspirada nos fantoches nordestinos. Uma experiência lúdica e regional que mistura arte popular e tecnologia em tempo real.',
            projectName: 'caixa_production_model_v21.json'
        },
    ];


    const isDesktop = useMediaQuery("(min-width: 1024px)");
    const btgerar = isDesktop ? BTGerarDesk : BTGerar;

    const [image, setImage] = useState<File | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement | null>(null);
    const [currentIndex, setCurrentIndex] = useState(0);
    const currentProject = projects[currentIndex];
    const [isPaused, setIsPaused] = useState(false);
    const [isAnimating, setIsAnimating] = useState(false);
    const [previousIndex, setPreviousIndex] = useState<number | null>(null);
    const navigate = useNavigate();


    const handleNext = () => {
        if (isAnimating) return;
        setIsAnimating(true);
        setPreviousIndex(currentIndex);
        setCurrentIndex((prev) => (prev + 1) % projects.length);
    };

    const handlePrevious = () => {
        if (isAnimating) return;
        setIsAnimating(true);
        setPreviousIndex(currentIndex);
        setCurrentIndex((prev) => (prev - 1 + projects.length) % projects.length);
    };


    const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        const file = e.dataTransfer.files[0];
        handleFile(file);
    };

    const handleFile = (file: File) => {
        if (file && file.type.startsWith('image/')) {
            setImage(file);
            setPreviewUrl(URL.createObjectURL(file));
        }
    };

    const handleClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0]);
        }
    };

    const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
    };

    const handleUpload = async () => {
        if (!image) return;

        try {
            const response = await uploadImage(image, currentProject.projectName);

            const jobId = response.request_id || response.job_id;

            if (!jobId) {
                throw new Error('ID do job não encontrado na resposta.');
            }

            localStorage.setItem('job_id', jobId);
            localStorage.setItem('bgBackground', currentProject.inputContainerColor);
            toast.success('Imagem enviada com sucesso!');
            navigate('/result');
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido';
            toast.error('Erro ao enviar job: ' + errorMessage);
            console.error('Erro ao enviar job:', error);
        }
    };

    useEffect(() => {
        if (isPaused) return;

        const interval = setInterval(() => {
            setIsAnimating(true);
            setTimeout(() => {
                setCurrentIndex((prev) => (prev + 1) % projects.length);
                setIsAnimating(false);
            }, 300);
        }, 10000);

        return () => clearInterval(interval);
    }, [isPaused, projects.length]);

    useEffect(() => {
        if (!isAnimating) return;

        const timer = setTimeout(() => {
            setIsAnimating(false);
            setPreviousIndex(null);
        }, 500);

        return () => clearTimeout(timer);
    }, [isAnimating]);

    return (
        <>
            <Styled.Container>

                <Styled.ImageBackgroundContainer>
                    <Header />
                    {previousIndex !== null && (
                        <Styled.ImageBackground
                            image={projects[previousIndex].imageBackground}
                            className="slide-out"
                        />
                    )}
                    <Styled.ImageBackground
                        image={currentProject.imageBackground}
                        className="slide-in"
                    />

                    <Styled.ArrowLeft onClick={handlePrevious}>
                        <img src={ArrowLeft} alt="Anterior" />
                    </Styled.ArrowLeft>

                    <Styled.ArrowRight onClick={handleNext}>
                        <img src={ArrowRight} alt="Próximo" />
                    </Styled.ArrowRight>

                    <Styled.CarouselIndicator>
                        {projects.map((_, index) => (
                            <Styled.Bullet
                                key={index}
                                active={index === currentIndex}
                                onClick={() => setCurrentIndex(index)}
                                style={{ cursor: 'pointer' }}
                            />
                        ))}
                    </Styled.CarouselIndicator>

                </Styled.ImageBackgroundContainer>

                <Styled.InputContainer
                    backgroundColor={currentProject.inputContainerColor}
                    onMouseEnter={() => setIsPaused(true)}
                    onMouseLeave={() => setIsPaused(false)}
                >
                    <Styled.InputContent>
                        <Styled.Texts>
                            <h1>{currentProject.tittleText}</h1>
                            <p>{currentProject.text}</p>
                        </Styled.Texts>

                        <Styled.InputItems>
                            <Styled.Input
                                onClick={handleClick}
                                onDrop={handleDrop}
                                onDragOver={handleDragOver}
                            >
                                {previewUrl ? (
                                    <img src={previewUrl} alt="preview" style={{ borderRadius: '15px', maxWidth: '100%', maxHeight: '100%' }} />
                                ) : (
                                    <>
                                        <img src={PlusButton} alt="" />
                                        <span>selecione um arquivo</span>
                                    </>
                                )}
                                <input
                                    type="file"
                                    accept="image/*"
                                    ref={fileInputRef}
                                    onChange={handleFileChange}
                                    style={{ display: 'none' }}
                                />
                            </Styled.Input>

                            <Styled.GenerateButton onClick={handleUpload}>
                                <img src={btgerar} alt="" />
                            </Styled.GenerateButton>
                        </Styled.InputItems>

                    </Styled.InputContent>



                </Styled.InputContainer>

            </Styled.Container >
            <Footer />
        </>
    );
};