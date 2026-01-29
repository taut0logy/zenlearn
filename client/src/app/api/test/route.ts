// create a route with a basic json response

export async function GET() {
    return new Response(JSON.stringify({ message: "Hello, world!" }));
}
