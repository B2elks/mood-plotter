import AVFoundation
#if os(iOS)
import UIKit
#endif

final class SoundManager {
    enum Surface: String {
        case block, trampoline, catapult, scoreZone, wall
    }

    var isMuted: Bool = false

    private let engine = AVAudioEngine()
    private var playerNodes: [AVAudioPlayerNode] = []
    private var nextNodeIndex = 0
    private var buffers: [String: AVAudioPCMBuffer] = [:]

    private static let frequencies: [Double] = [
        523.25,  // C5  — pink (index 0)
        587.33,  // D5  — orange (index 1)
        659.25,  // E5  — green (index 2)
        783.99,  // G5  — purple (index 3)
        880.00,  // A5  — yellow (index 4)
    ]

    private static let surfaces: [Surface] = [.block, .trampoline, .catapult, .scoreZone, .wall]
    private static let polyphony = 8

    init() {
        configureAudioSession()

        let format = AVAudioFormat(standardFormatWithSampleRate: 44100, channels: 1)!

        // Pre-render all 25 buffers.
        for (colorIndex, freq) in Self.frequencies.enumerated() {
            for surface in Self.surfaces {
                let buffer = synthesize(frequency: freq, surface: surface, format: format)
                buffers[Self.key(colorIndex: colorIndex, surface: surface)] = buffer
            }
        }

        // Wire up player-node pool.
        for _ in 0..<Self.polyphony {
            let node = AVAudioPlayerNode()
            engine.attach(node)
            engine.connect(node, to: engine.mainMixerNode, format: format)
            playerNodes.append(node)
        }

        do {
            try engine.start()
            for node in playerNodes { node.play() }
        } catch {
            print("SoundManager: AVAudioEngine failed to start: \(error)")
        }
    }

    func play(colorIndex: Int, surface: Surface) {
        guard !isMuted else { return }
        let safeIndex = max(0, min(colorIndex, Self.frequencies.count - 1))
        let key = Self.key(colorIndex: safeIndex, surface: surface)
        guard let buffer = buffers[key] else { return }

        let node = playerNodes[nextNodeIndex]
        nextNodeIndex = (nextNodeIndex + 1) % playerNodes.count

        // Stop any in-flight buffer on this node so we don't queue up.
        node.stop()
        node.scheduleBuffer(buffer, at: nil, options: [], completionHandler: nil)
        node.play()
    }

    private static func key(colorIndex: Int, surface: Surface) -> String {
        "\(colorIndex)-\(surface.rawValue)"
    }

    private func configureAudioSession() {
        #if os(iOS)
        try? AVAudioSession.sharedInstance().setCategory(.ambient, mode: .default)
        try? AVAudioSession.sharedInstance().setActive(true)
        #endif
    }

    private func synthesize(frequency: Double, surface: Surface, format: AVAudioFormat) -> AVAudioPCMBuffer {
        let sampleRate = format.sampleRate
        let duration: Double
        let gain: Double
        switch surface {
        case .block:      duration = 0.15; gain = 0.55
        case .trampoline: duration = 0.25; gain = 0.55
        case .catapult:   duration = 0.20; gain = 0.65
        case .scoreZone:  duration = 0.60; gain = 0.55
        case .wall:       duration = 0.08; gain = 0.30
        }

        let totalFrames = AVAudioFrameCount(sampleRate * duration)
        let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: totalFrames)!
        buffer.frameLength = totalFrames
        let samples = buffer.floatChannelData![0]

        var phase: Double = 0
        for frame in 0..<Int(totalFrames) {
            let t = Double(frame) / sampleRate
            let progress = t / duration  // 0..1

            // Per-surface envelope.
            let envelope: Double
            switch surface {
            case .block:
                envelope = exp(-t / (duration * 0.30))
            case .trampoline:
                envelope = exp(-t / (duration * 0.50))
            case .catapult:
                let attack = min(1.0, t / 0.005)  // 5 ms ramp
                envelope = attack * exp(-t / (duration * 0.40))
            case .scoreZone:
                let attack = min(1.0, t / 0.020)  // 20 ms ramp
                envelope = attack * exp(-t / (duration * 0.60))
            case .wall:
                envelope = exp(-t / (duration * 0.30))
            }

            // Per-surface instantaneous frequency.
            let f: Double
            switch surface {
            case .block, .scoreZone:
                f = frequency
            case .trampoline:
                f = frequency * (1.0 + 0.5 * sin(.pi * progress))
            case .catapult, .wall:
                f = frequency * 0.5
            }

            phase += 2 * .pi * f / sampleRate

            // Per-surface waveform (mostly sine, scoreZone adds a fifth).
            let core: Double
            switch surface {
            case .scoreZone:
                core = sin(phase) * 0.6 + sin(phase * 1.5) * 0.4
            default:
                core = sin(phase)
            }

            samples[frame] = Float(core * envelope * gain)
        }

        return buffer
    }
}
