export interface Config {
    workingDirectory: string;
    model?: string;
    systemPrompt?: string;
}
export declare function loadConfig(): Config;
export declare function saveConfig(config: Config): void;
