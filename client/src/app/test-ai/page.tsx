"use client";

import { useState } from "react";
import axios from "axios";

export default function TestAIPage() {
    const [prompt, setPrompt] = useState("");
    const [response, setResponse] = useState("");
    const [loading, setLoading] = useState(false);

    const handleGenerate = async () => {
        try {
            setLoading(true);
            setResponse("");

            const res = await axios.post("http://localhost:8000/api/v1/test-ai", {
                prompt: prompt,
            });
            setResponse(res.data.response);
        } catch (error) {
            console.error("Error generating response:", error);
            setResponse("Error generating response. Check console.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-screen p-4 gap-4">
            <h1 className="text-2xl font-bold">AI Verification Test</h1>
            <div className="w-full max-w-md flex flex-col gap-2">
                <textarea
                    className="w-full p-2 border rounded"
                    rows={4}
                    placeholder="Enter your prompt here..."
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                />
                <button
                    className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50"
                    onClick={handleGenerate}
                    disabled={loading || !prompt}
                >
                    {loading ? "Generating..." : "Generate Response"}
                </button>
            </div>
            {response && (
                <div className="w-full max-w-md p-4 bg-gray-100 dark:bg-gray-800 rounded mt-4">
                    <h2 className="font-semibold mb-2">Response:</h2>
                    <p className="whitespace-pre-wrap">{response}</p>
                </div>
            )}
        </div>
    );
}
