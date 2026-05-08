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
                        System.out.println("a member has left the chat");
                        break;
                    case GETSTATUS:
                        GetJoinStatus status = value.getGetStatus().getStatus();
                        if (status == GetJoinStatus.NAME_TAKEN) {
                            System.out.println("Error: Name already taken");
                        }else if(status == GetJoinStatus.CHAT_FULL) {
                            System.out.println("Error: Chat already full");
                        }else{
                            System.out.println("Successfully joined");
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

    public static void main(String[] args) {
        ManagedChannel channel = Grpc.newChannelBuilder("localhost:50051", InsecureChannelCredentials.create()).build();
        myClient client = new myClient(channel);
        client.startChat();

        Scanner scanner = new Scanner(System.in);
        System.out.print("insert nickname: ");
        String name = scanner.nextLine();

        // 1. send JOIN
        MemberOptions joinReq = MemberOptions.newBuilder()
            .setJoin(JoinChat.newBuilder().setNickname(name).build())
            .build();
        client.requestObserver.onNext(joinReq);

        // 2. chat loop
        while (true) {
            String input = scanner.nextLine();
            if (input.equalsIgnoreCase("!Exit")) {
                MemberOptions leaveRequest = MemberOptions.newBuilder()
                    .setLeave(LeaveChat.newBuilder().build())
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