package fra.hostjava;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.File;
import java.util.HashSet;
import java.util.Set;

@Component
public class FunctionConfigLoader {
    private final Set<String> javaFunctions = new HashSet<>();

    public FunctionConfigLoader(@Value("${functions.config.path}") String path) throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        JsonNode root = mapper.readTree(new File(path));
        for (JsonNode node : root.get("functions")) {
            if ("host-java".equals(node.get("host_service").asText())) {
                javaFunctions.add(node.get("name").asText());
            }
        }
    }

    public boolean exists(String functionName) {
        return javaFunctions.contains(functionName);
    }
}
