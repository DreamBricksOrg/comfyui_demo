import styled from "styled-components";

interface ContainerProps {
  backgroundColor?: string;
}

export const Container = styled.div<ContainerProps>`
  font-family: Araboto-Bold, sans-serif;
  text-align: center;
  height: 100%;
  background-color: ${(props) => props.backgroundColor || "#34aed3"};
`;

export const Content = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;

  h1 {
    margin-top: 100px;
    font-size: 2em;
    margin-bottom: 40px;
    color: white;

    @media (min-width: 768px) {
      font-size: 3em;
    }
  }
`;

export const Status = styled.div`
  font-size: 1.2em;
  margin-bottom: 20px;
  color: black;
`;

export const Result = styled.div`
  img {
    max-width: 330px;
    height: auto;
    border: 1px solid #ccc;
    box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
    cursor: pointer;

    @media (min-width: 768px) {
      max-width: 400px;
    }
  }
`;

export const ButtonsContainer = styled.div`
  margin: 50px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 30px;
`;

export const BackButton = styled.button`
  font-family: Araboto-Bold, sans-serif;
  padding: 10px 20px;
  width: 230px;
  font-size: 1.4rem;
  background-color: white;
  color: #007bff;
  border: none;
  border-radius: 16px;
  cursor: pointer;

  &:hover {
    background-color: #ccc;
  }
`;

export const LoadingCard = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  border-radius: 10px;
  background: white;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);
  width: 300px;
  gap: 50px;
  margin: 0 auto;
`;

export const SpinnerWrapper = styled.div`
  position: relative;
  margin-top: 20px;
  width: 32px;
  height: 32px;

  &:after {
    content: "";
    background: #34aed3;
    position: absolute;
    left: 50%;
    top: 50%;
    width: 32px;
    height: 32px;
    border-radius: 4px;
    transform-origin: -16px -32px;
    animation: rotate 1s linear infinite;
  }

  @keyframes rotate {
    0%,
    100% {
      transform: rotate(-45deg) translate(-50%, -50%);
    }
    50% {
      transform: rotate(-245deg) translate(-50%, -50%);
    }
  }
`;

export const CenteredWrapper = styled.div`
  display: flex;
  height: 80vh;
  justify-content: center;
  align-items: center;
`;

export const ImageOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.7);
  z-index: 9999;
  display: flex;
  justify-content: center;
  align-items: center;

  img {
    max-width: 50%;
    max-height: 50%;
    transform: scale(1.5);
    transition: transform 0.3s ease;
    border: 2px solid #fbac26;
    box-shadow: 0 0 30px rgba(0, 0, 0, 0.6);
  }
`;
