import React, { Component } from "react";
import styled, { css } from "styled-components";

function CupertinoButtonBlueTextColor1(props) {
  return (
    <Container {...props}>
      <ForgotPassword>Forgot Password?</ForgotPassword>
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

const ForgotPassword = styled.span`
  font-family: Roboto;
  color: #007AFF;
  font-size: 17px;
  font-weight: 500;
`;

export default CupertinoButtonBlueTextColor1;
