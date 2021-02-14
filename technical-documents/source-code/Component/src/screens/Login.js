import React, { Component } from "react";
import styled, { css } from "styled-components";
import FontAwesomeIcon from "react-native-vector-icons/dist/FontAwesome";
import EntypoIcon from "react-native-vector-icons/dist/Entypo";
import { Link } from "react-router-dom";

function Login(props) {
  return (
    <>
      <Text>Sign In</Text>
      <IconRow>
        <FontAwesomeIcon
          name="user"
          style={{
            color: "rgba(128,128,128,1)",
            fontSize: 40
          }}
        ></FontAwesomeIcon>
        <UsernameColumn>
          <Username>Username</Username>
          <Rect></Rect>
        </UsernameColumn>
      </IconRow>
      <Icon2Row>
        <EntypoIcon
          name="lock"
          style={{
            color: "rgba(128,128,128,1)",
            fontSize: 40
          }}
        ></EntypoIcon>
        <PasswordColumn>
          <Password>Password</Password>
          <Rect1></Rect1>
        </PasswordColumn>
      </Icon2Row>
      <NextButton>
        <Link to="/Login">
          <Button>
            <ButtonOverlay>
              <Next>Next</Next>
            </ButtonOverlay>
          </Button>
        </Link>
      </NextButton>
      <ForgotPassword>Forgot Password?</ForgotPassword>
    </>
  );
}

const Text = styled.span`
  font-family: Roboto;
  font-style: normal;
  font-weight: 400;
  color: #121212;
  font-size: 40px;
  margin-top: 201px;
  margin-left: 127px;
`;

const ButtonOverlay = styled.button`
 display: block;
 background: none;
 height: 100%;
 width: 100%;
 border:none
 `;
const Username = styled.span`
  font-family: Roboto;
  font-style: normal;
  font-weight: 400;
  color: #121212;
`;

const Rect = styled.div`
  width: 194px;
  height: 6px;
  background-color: #E6E6E6;
  margin-top: 17px;
`;

const UsernameColumn = styled.div`
  width: 194px;
  flex-direction: column;
  display: flex;
  margin-left: 14px;
`;

const IconRow = styled.div`
  height: 40px;
  flex-direction: row;
  display: flex;
  margin-top: 40px;
  margin-left: 72px;
  margin-right: 66px;
`;

const Password = styled.span`
  font-family: Roboto;
  font-style: normal;
  font-weight: 400;
  color: #121212;
`;

const Rect1 = styled.div`
  width: 194px;
  height: 6px;
  background-color: #E6E6E6;
  margin-top: 21px;
`;

const PasswordColumn = styled.div`
  width: 194px;
  flex-direction: column;
  display: flex;
  margin-left: 9px;
`;

const Icon2Row = styled.div`
  height: 44px;
  flex-direction: row;
  display: flex;
  margin-top: 20px;
  margin-left: 66px;
  margin-right: 66px;
`;

const NextButton = styled.div`
  width: 41px;
  height: 24px;
  flex-direction: column;
  display: flex;
  margin-top: 75px;
  margin-left: 167px;
`;

const Button = styled.div`
  width: 100px;
  height: 44px;
  background-color: rgba(0,122,255,1);
  flex-direction: column;
  border-radius: 5px;
  margin-top: -11px;
  margin-left: -29px;
  border: none;
`;

const Next = styled.span`
  font-family: Roboto;
  font-style: normal;
  font-weight: 400;
  color: rgba(255,255,255,1);
  font-size: 20px;
  margin-top: 11px;
  margin-left: 29px;
`;

const ForgotPassword = styled.span`
  font-family: Roboto;
  font-style: normal;
  font-weight: 400;
  color: rgba(0,122,255,1);
  margin-top: -72px;
  margin-left: 131px;
`;

export default Login;
