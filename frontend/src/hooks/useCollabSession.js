import { useEffect, useMemo, useState } from "react";
import { runCode } from "../services/api";
import { getSocket } from "../services/socketClient";

export function useCollabSession() {
  const [roomId] = useState("room-1234");
  const [username] = useState("You");
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState("print('Hello from Code Collab')");
  const [messages, setMessages] = useState([]);
  const [users, setUsers] = useState(["You"]);
  const [output, setOutput] = useState("Ready. Click Run to execute code.");

  const socket = useMemo(() => getSocket(), []);

  useEffect(() => {
    socket.emit("join_room", { room_id: roomId, username });

    socket.on("room_state", (state) => {
      if (state?.code) setCode(state.code);
      if (Array.isArray(state?.users)) setUsers(state.users);
      if (Array.isArray(state?.messages)) setMessages(state.messages);
    });

    socket.on("code_change", (payload) => {
      if (typeof payload?.code === "string") setCode(payload.code);
      if (typeof payload?.language === "string") setLanguage(payload.language);
    });

    socket.on("send_message", (payload) => setMessages((prev) => [...prev, payload]));
    socket.on("user_join", (payload) => Array.isArray(payload?.users) && setUsers(payload.users));
    socket.on("user_leave", (payload) => Array.isArray(payload?.users) && setUsers(payload.users));

    return () => {
      socket.emit("leave_room", { room_id: roomId, username });
      socket.off("room_state");
      socket.off("code_change");
      socket.off("send_message");
      socket.off("user_join");
      socket.off("user_leave");
    };
  }, [roomId, socket, username]);

  const updateCode = (nextCode) => {
    setCode(nextCode);
    socket.emit("code_change", { room_id: roomId, language, code: nextCode });
  };

  const sendMessage = (message) => {
    if (!message.trim()) return;
    const payload = { username, message };
    setMessages((prev) => [...prev, payload]);
    socket.emit("send_message", { room_id: roomId, username, message });
  };

  const executeCode = async () => {
    try {
      setOutput("Running...");
      const response = await runCode(language, code);
      setOutput(response.output || "No output.");
    } catch (error) {
      setOutput(error?.response?.data?.error || error.message || "Execution failed.");
    }
  };

  return {
    roomId,
    language,
    setLanguage,
    code,
    updateCode,
    users,
    messages,
    sendMessage,
    output,
    executeCode,
  };
}
