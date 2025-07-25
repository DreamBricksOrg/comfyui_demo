import styled from "styled-components";

export const Container = styled.div`
  display: flex;
  height: 80px;
  width: 100%;
  background-color: #34aed3;
  position: relative;
`;

export const Jobson = styled.img`
  position: absolute;
  max-width: 80px;
  height: auto;
  object-fit: contain;
  transform: translate(-50%, -50%);
  top: 9%;
  left: 80px;
`;
