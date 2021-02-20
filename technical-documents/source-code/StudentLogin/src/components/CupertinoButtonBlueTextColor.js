import React, { Component } from "react";
import styled, { css } from "styled-components";

function CupertinoButtonBlueTextColor(props) {
  return (
    <Container {...props}>
      <Caption>Button</Caption>
    </Container>
  );
}

const Container = styled.div`
  display: flex;
  background-color: transparent;
  justify-content: center;
  align-items: center;
  flex-direction: row;
  border-radius: 5px;
`;

const Caption = styled.span`
  font-family: Roboto;
  color: #007AFF;
  font-size: 17px;
  font-weight: 500;
`;

export default CupertinoButtonBlueTextColor;
