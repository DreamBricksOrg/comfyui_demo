import styled from "styled-components";

export const Container = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100px;
  width: 100%;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0));
  position: absolute;
  top: 0;
  left: 0;
  z-index: 2;
`;

export const Logo = styled.img`
  max-height: 60%;
  height: auto;
  object-fit: contain;
`;
