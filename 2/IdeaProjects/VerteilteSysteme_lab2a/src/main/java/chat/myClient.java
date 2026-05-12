package chat;

import com.google.protobuf.Empty;
import io.grpc.Channel;
import io.grpc.Grpc;
import io.grpc.InsecureChannelCredentials;
import io.grpc.ManagedChannel;
import io.grpc.stub.StreamObserver;

import java.util.Scanner;

public class myClient {
    private final ChatServiceGrpc.ChatServiceStub asyncStub;
    private final ChatServiceGrpc.ChatServiceBlockingStub blockingStub;
    private StreamObserver<MemberOptions> requestObserver;

    private volatile boolean joinFailed = false;
    private volatile boolean isRegistered = false;

    public void resetJoin(){
        joinFailed = false;
    }

    public myClient(Channel channel){
        asyncStub = ChatServiceGrpc.newStub(channel);
        blockingStub = ChatServiceGrpc.newBlockingStub(channel);
    }

    public void startChat(){
        StreamObserver<MemberOptions> responseObserver = new StreamObserver<MemberOptions>() {
            @Override
            public void onNext(MemberOptions value) {
                switch(value.getOptionTypeCase()){
                    case JOIN:
                        System.out.println(value.getJoin().getNickname() + " has joined.");
                        break;
                    case SEND:
                        System.out.println(value.getSend().getNickname() + ": " + value.getSend().getText());
                        break;
                    case LEAVE:
                        System.out.println(value.getLeave().getNickname() + " has left the chat");
                        break;
                    case GETSTATUS:
                        GetJoinStatus status = value.getGetStatus().getStatus();
                        if (status == GetJoinStatus.NAME_TAKEN) {
                            System.out.println("Error: Name already taken");
                            isRegistered = false;
                            joinFailed = true;
                        }else if(status == GetJoinStatus.CHAT_FULL) {
                            System.out.println("Error: Chat already full");
                            isRegistered = false;
                            joinFailed = true;
                        }else if (status == GetJoinStatus.SUCCESS){
                            System.out.println("Successfully joined");
                            isRegistered = true;
                            joinFailed = false;
                        }
                        break;
                    default:
                        break;
                }

            }

            @Override
            public void onError(Throwable throwable) {
                throwable.printStackTrace();
            }

            @Override
            public void onCompleted() {
                System.out.println("Connection end");
            }
        };

        this.requestObserver = asyncStub.registerStream(responseObserver);
    }

    public static void main(String[] args) throws InterruptedException {
        ManagedChannel channel = Grpc.newChannelBuilder("localhost:50051", InsecureChannelCredentials.create()).build();
        myClient client = new myClient(channel);
        client.startChat();
        Scanner scanner = new Scanner(System.in);
        String name = "";

        while(!client.isRegistered){
            System.out.print("insert nickname: ");
            name = scanner.nextLine();
            client.resetJoin();

            // 1. send JOIN
            MemberOptions joinReq = MemberOptions.newBuilder()
                    .setJoin(JoinChat.newBuilder().setNickname(name).build())
                    .build();
            client.requestObserver.onNext(joinReq);

            int timeout = 0;
            while(!client.isRegistered && !client.joinFailed && timeout < 20){
                Thread.sleep(100);
                timeout++;
            }

            if(!client.isRegistered) {
                System.out.println("Retry with another name...");
            }
        }

        // 2. chat loop
        while (true) {
            String input = scanner.nextLine();
            if (input.equalsIgnoreCase("!Exit")) {
                MemberOptions leaveRequest = MemberOptions.newBuilder()
                    .setLeave(LeaveChat.newBuilder().setNickname(name).build())
                    .build();
                client.requestObserver.onNext(leaveRequest);
                client.requestObserver.onCompleted();
                break;
            }

            if (input.equalsIgnoreCase("!List")) {
                try {
                    MemberList list = client.blockingStub.getMemberList(Empty.newBuilder().build());
                    System.out.println("active Members:");
                    list.getMembersList().forEach(m -> System.out.println("- " + m.getNickname()));
                } catch (Exception e) {
                    System.err.println("Error when calling List: " + e.getMessage());
                }
                continue;
            }

            // send messages
            MemberOptions msgReq = MemberOptions.newBuilder()
                    .setSend(ChatMsg.newBuilder()
                            .setNickname(name).
                            setText(input).
                            build())
                    .build();
            client.requestObserver.onNext(msgReq);
        }
        channel.shutdown();
    }

}