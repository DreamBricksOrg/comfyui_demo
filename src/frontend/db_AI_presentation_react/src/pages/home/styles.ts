import styled from "styled-components";

interface ImageBackgroundProps {
  image: string;
}

interface InputContainerProps {
  backgroundColor?: string;
}

export const Container = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100vh;

  @media (min-width: 1024px) {
    flex-direction: row-reverse;
  }
`;

export const ImageBackgroundContainer = styled.div`
  height: 50%;
  position: relative;

  @media (min-width: 1024px) {
    height: 100%;
    width: 60%;
  }
`;

export const ArrowLeft = styled.div`
  position: absolute;
  top: 50%;
  left: 10px;
  height: 40px;
  width: 40px;
  border-radius: 360px;
  background-color: #0c495d;
  display: flex;
  justify-content: center;
  align-items: center;

  img {
    height: 80%;
  }

  &:hover {
    cursor: pointer;
    background-color: #34aed3;
  }
`;

export const ArrowRight = styled.div`
  position: absolute;
  top: 50%;
  right: 10px;
  height: 40px;
  width: 40px;
  border-radius: 360px;
  background-color: #0c495d;
  display: flex;
  justify-content: center;
  align-items: center;

  img {
    height: 80%;
  }

  &:hover {
    cursor: pointer;
    background-color: #34aed3;
  }
`;

export const CarouselIndicator = styled.div`
  background-color: #fff;
  border-radius: 20px;
  padding: 5px 40px;
  position: absolute;
  bottom: 20px;
  right: 50%;
  transform: translate(50%, 50%);
  display: flex;
  justify-content: center;
  gap: 8px;
`;

export const Bullet = styled.div<{ active: boolean }>`
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: ${({ active }) => (active ? "#34AED3" : "#034A5D")};
  transition: background-color 0.3s ease;
`;

export const ImageBackground = styled.div<ImageBackgroundProps>`
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 100%;
  background-image: url(${(props) => props.image});
  background-size: cover;
  background-repeat: no-repeat;
  background-position: center;
  transition: all 0.5s ease;
  opacity: 0;

  &.slide-in {
    animation: fadeIn 0.5s forwards;
  }

  &.slide-out {
    animation: fadeOut 0.5s forwards;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes fadeOut {
    from {
      opacity: 1;
    }
    to {
      opacity: 0;
    }
  }
`;

export const InputContainer = styled.div<InputContainerProps>`
  height: 50%;
  width: 100%;
  background-color: ${(props) => props.backgroundColor || "#2b5234"};
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-end;
  gap: 20px;
  transition: background-color 0.5s ease;

  @media (min-width: 1024px) {
    height: 100%;
    width: 40%;
  }
`;

export const InputContent = styled.div`
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  justify-content: space-between;

  @media (min-width: 1024px) {
    flex-direction: column;
    gap: 50px;
  }
`;

export const Texts = styled.div`
  padding-left: 10px;
  overflow: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
  max-height: 230px;

  h1 {
    font-family: Araboto-Bold;
    font-size: 1.5rem;
    line-height: 1;
    padding-bottom: 20px;

    @media (min-width: 1024px) {
      font-size: 5rem;
    }
  }

  p {
    font-size: 0.8rem;
    text-align: justify;

    @media (min-width: 1024px) {
      font-size: 1rem;
    }
  }

  @media (min-width: 1024px) {
    padding-left: 50px;
    width: 90%;
    max-height: 320px;
  }
`;

export const InputItems = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-end;
  width: 100%;

  @media (min-width: 1024px) {
    gap: 80px;
    align-items: flex-start;
  }
`;

export const Input = styled.div`
  margin: 10px;
  width: 180px;
  height: 160px;
  border: 2px solid white;
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  cursor: pointer;
  overflow: hidden;

  img {
    max-width: 100%;
    max-height: 100%;
    object-fit: cover;
    border-radius: 15px;
  }

  span {
    font-size: 0.8rem;
    font-family: Araboto-Bold;
    text-align: center;

    @media (min-width: 1024px) {
      font-size: 1rem;
    }
  }

  @media (min-width: 1024px) {
    margin-left: 180px;
    width: 300px;
    height: 240px;
    border: 4px solid white;
  }
`;

export const GenerateButton = styled.div`
  margin-top: 10px;
  cursor: pointer;
`;
