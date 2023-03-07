import { useState, useEffect } from "react";
import reactLogo from "./assets/react.svg";
import "./App.css";
import FortuneView from "./components/FortuneView";
import InitialButton from "./components/InitialButton";
import ClarityView from "./components/ClarityView";

function App() {
  // Set Up State
  const [fortune, setFortune] = useState("");
  const [question, setQuestion] = useState("");
  const [questionAnswer, setQuestionAnswer] = useState("");
  const [stateGathered, setStateGathered] = useState(false);
  const [isButtonShown, setIsButtonShown] = useState(true);
  const [isFortuneShown, setIsFortuneShown] = useState(false);
  const [isClarityShown, setIsClarityShown] = useState(false);
  const [timeToNextOracle, setTimeToNextOracle] = useState(0);

  // Set up functions
  const handleSubmitQuestion = async (event) => {
    event.preventDefault();
    setIsFortuneShown(false);
    setIsClarityShown(true);
    console.log("clarity submitted");
    const resp = await getAnswers(question, fortune, setQuestionAnswer);
    console.log("clarity gained");
    await updateRemoteState(
      fortune,
      question,
      false,
      false,
      true,
      timeToNextOracle,
      resp
    );
    console.log("clarity updated");
  };

  const handleInputChange = (event) => {
    setQuestion(event.target.value);
  };

  const handleButtonPress = async () => {
    setIsButtonShown(false);
    setIsFortuneShown(true);
    setTimeToNextOracle(Date.now() + 86400000);

    const fortune = await getFortune(setFortune);
    updateRemoteState(
      fortune,
      "",
      false,
      true,
      false,
      Date.now() + 86400000,
      questionAnswer
    );
  };
  initialise_vibes(
    setFortune,
    setIsButtonShown,
    setIsFortuneShown,
    setIsClarityShown,
    setTimeToNextOracle,
    setStateGathered,
    setQuestionAnswer,
    setQuestion
  );

  return (
    <div className="layer1">
      {stateGathered && (
        <div>
          <InitialButton
            isButtonShown={isButtonShown}
            handleButtonPress={handleButtonPress}
          />
          <FortuneView
            fortune={fortune}
            question={question}
            handleSubmitQuestion={handleSubmitQuestion}
            handleInputChange={handleInputChange}
            isFortuneShown={isFortuneShown}
          />
          <ClarityView
            fortune={fortune}
            question={question}
            isClarityShown={isClarityShown}
            questionAnswer={questionAnswer}
            epochTime={timeToNextOracle}
          />
        </div>
      )}
    </div>
  );
}

export default App;

const initialise_vibes = (
  setFortune,
  setIsButtonShown,
  setIsFortuneShown,
  setIsClarityShown,
  setTimeToNextOracle,
  setStateGathered,
  setQuestionAnswer,
  setQuestion
) =>
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch("/api/get_initial_vibe");
        const data = await response.json();
        setFortune(data.fortune);
        setQuestion(data.question);
        setIsButtonShown(data.isButtonShown);
        setIsFortuneShown(data.isFortuneShown);
        setIsClarityShown(data.isClarityShown);
        setTimeToNextOracle(data.timeToNextOracle);
        setQuestionAnswer(data.answer);
        setStateGathered(true);
      } catch (error) {
        console.error("Error:", error);
      }
    };
    fetchData();
  }, []);

const getAnswers = async (question, fortune, setQuestionAnswer) => {
  const response = await fetch("/api/clarify_vibes", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      fortune,
    }),
  });
  const data = await response.json();
  setQuestionAnswer(data.answer);
  return data.answer;
};

const updateRemoteState = async (
  fortune,
  question,
  isButtonShown,
  isFortuneShown,
  isClarityShown,
  timeToNextOracle,
  questionAnswer
) => {
  console.log(question);
  await fetch("/api/update_state", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      fortune: fortune,
      question: question,
      isButtonShown: isButtonShown,
      isFortuneShown: isFortuneShown,
      isClarityShown: isClarityShown,
      timeToNextOracle: timeToNextOracle,
      answer: questionAnswer,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((data) => {
      console.log("Update state response:", data);
      // Handle the response data as needed
    })
    .catch((error) => {
      console.error("There was a problem with the fetch operation:", error);
      // Handle the error as needed
    });
};

const getFortune = async (setFortune) => {
  try {
    const response = await fetch("/api/get_fortune");
    const data = await response.json();
    console.log(data.fortune);
    setFortune(data.fortune);
    return data.fortune;
  } catch (error) {
    console.error("Error getting fortune:", error);
  }
};
